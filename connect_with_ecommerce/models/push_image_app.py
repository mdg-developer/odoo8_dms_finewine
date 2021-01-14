from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import timedelta,datetime
import calendar
from pyfcm import FCMNotification

class PushImageApp(osv.osv):
    _name = "push.image.app"
    
    _columns = {
               'name':fields.char(string='Name'),      
               'date':fields.datetime('Date'),         
            }
    
    _defaults = {
        'date': fields.datetime.now,
    } 
     
    def create(self, cursor, user, vals, context=None):
        
        fcm_api_key = self.pool.get('ir.config_parameter').get_param(cursor, user, 'retail_fcm_api_key', default=False, context=context)
        if fcm_api_key:
            push_service = FCMNotification(api_key=fcm_api_key)
            result = push_service.notify_topic_subscribers(topic_name="image_changes", message_body="New images are coming up!")
        return super(PushImageApp, self).create(cursor, user, vals, context=context)
    