# -*- coding: utf-8 -*-
from .main import *

_logger = logging.getLogger(__name__)


# List of REST resources in current file:
#   (url prefix)        (method)        (action)
# /api/report/<method>  PUT         - Call method (with optional parameters)


# List of IN/OUT data (json data and HTTP-headers) for each REST resource:

# /api/report/<method>  PUT  - Call method (with optional parameters)
# IN data:
#   HEADERS:
#       'access_token'
#   JSON:
#       (named parameters of method)                # editable
#           ...
# OUT data:
OUT__report__call_method__SUCCESS_CODE = 200        # editable
#   Possible ERROR CODES:
#       401 'invalid_token'
#       400 'no_access_token'
#       501 'method_not_exist_in_odoo'
#       409 'not_called_method_in_odoo'


# HTTP controller of REST resources:

class ControllerREST(http.Controller):
    
    # Call method (with parameters):
    @http.route('/api/report/<method>', methods=['PUT'], type='http', auth='none', csrf=False)
    @check_permissions
    def api__report__method_PUT(self, method, **kw):
        return wrap__resource__call_method(
            modelname = 'report',
            id = '-1',
            method = method,
            success_code = OUT__report__call_method__SUCCESS_CODE
        )
