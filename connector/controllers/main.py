import logging
import traceback
from cStringIO import StringIO
import time
from psycopg2 import OperationalError

import openerp
from openerp import _, http, tools
from openerp.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY

from ..session import ConnectorSessionHandler
from ..queue.job import (OpenERPJobStorage,
                         ENQUEUED)
from ..exception import (NoSuchJobError,
                         NotReadableJobError,
                         RetryableJobError,
                         FailedJobError,
                         NothingToDoJob)

_logger = logging.getLogger(__name__)

PG_RETRY = 30  # seconds


# TODO: perhaps the notion of ConnectionSession is less important
#       now that we are running jobs inside a normal Odoo worker


class RunJobController(http.Controller):

    job_storage_class = OpenERPJobStorage

    def _load_job(self, session, job_uuid):
        """ Reload a job from the backend """
        try:
            job = self.job_storage_class(session).load(job_uuid)
        except NoSuchJobError:
            # just skip it
            job = None
        except NotReadableJobError:
            _logger.exception('Could not read job: %s', job_uuid)
            raise
        return job
    
    def _dead_job(self, session, job_uuid):
        """ Reload a job from the backend """
        try:
            job = self.job_storage_class(session).exists_deadlock(job_uuid)
        except NoSuchJobError:
            # just skip it
            job = None
        except NotReadableJobError:
            _logger.exception('Could not read job: %s', job_uuid)
            raise
        return job  
        

    def _try_perform_job(self, session_hdl, job):
        """Try to perform the job."""

        # if the job has been manually set to DONE or PENDING,
        # or if something tries to run a job that is not enqueued
        # before its execution, stop
        if job.state != ENQUEUED:
            _logger.warning('job %s is in state %s '
                            'instead of enqueued in /runjob',
                            job.uuid, job.state)
            return

        with session_hdl.session() as session:
            # TODO: set_started should be done atomically with
            #       update queue_job set=state=started
            #       where state=enqueid and id=
            job.set_started()
            self.job_storage_class(session).store(job)

        _logger.debug('%s started', job)
        with session_hdl.session() as session:
            job.perform(session)
            job.set_done()
            self.job_storage_class(session).store(job)
        _logger.debug('%s done', job)


    def _try_deadlog_job(self, session_hdl, job):
        """Try to perform the job."""

        # if the job has been manually set to DONE or PENDING,
        # or if something tries to run a job that is not enqueued
        # before its execution, stop

        with session_hdl.session() as session:
            # TODO: set_started should be done atomically with
            #       update queue_job set=state=started
            #       where state=enqueid and id=
            self.job_storage_class(session).exists_deadlock(job)
        
    @http.route('/connector/runjob', type='http', auth='none')
    def runjob(self, db, job_uuid, **kw):

        session_hdl = ConnectorSessionHandler(db,
                                              openerp.SUPERUSER_ID)

        def retry_postpone(job, message, seconds=None):
            with session_hdl.session() as session:
                try:
                    job.postpone(result=message, seconds=seconds)
                    job.set_pending(reset_retry=False)
                    self.job_storage_class(session).store(job)
                except NothingToDoJob as err:
                    time.sleep(10)
                    retry_postpone(job, message, seconds);			
                    _logger.debug('%s %s job retry postpond error.', job, err)
                    
        with session_hdl.session() as session:
            job = self._load_job(session, job_uuid)
            if job is None:
                return ""

        try:
            try:
                #TODO,phyo  checking no concurrent errror and proceed.
                if  self._try_deadlog_job(session_hdl, job):
                    retry_postpone(job, tools.ustr("DB Concurrent happening and waiting", errors='replace'),
                               seconds=PG_RETRY)
                    _logger.debug('%s DB Concurrent and dead lock error or db busy and postpond job to 30secons postponed', job)
                else:
                    #No Dead lock in jobs, we proceed perform.
                    self._try_perform_job(session_hdl, job)
                    _logger.debug('%s job performing.', job)

                    

            except OperationalError as err:
                # Automatically retry the typical transaction serialization
                # errors
                if err.pgcode not in PG_CONCURRENCY_ERRORS_TO_RETRY:
                    raise
                try:
                    retry_postpone(job, tools.ustr(err.pgerror, errors='replace'),
                               seconds=PG_RETRY)
                    _logger.debug('%s OperationalError, postponed', job)
                except NothingToDoJob as err:
                        retry_postpone(job, tools.ustr(err.pgerror, errors='replace'),
                               seconds=PG_RETRY)
                        _logger.debug('%s postponed',job)

        except NothingToDoJob as err:
            if unicode(err):
                msg = unicode(err)
            else:
                msg = _('Job interrupted and set to Done: nothing to do.')
            job.set_done(msg)
            with session_hdl.session() as session:
                self.job_storage_class(session).store(job)

        except RetryableJobError as err:
            # delay the job later, requeue
            retry_postpone(job, unicode(err), seconds=err.seconds)
            _logger.debug('%s postponed', job)

        except (FailedJobError, Exception):
            buff = StringIO()
            traceback.print_exc(file=buff)
            _logger.error(buff.getvalue())

            job.set_failed(exc_info=buff.getvalue())
            with session_hdl.session() as session:
                self.job_storage_class(session).store(job)
            raise

        return ""
