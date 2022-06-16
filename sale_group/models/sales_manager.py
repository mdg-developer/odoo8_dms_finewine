import datetime
from lxml import etree
import math
import pytz
import urlparse
import openerp
from openerp import tools, api
from openerp.osv import osv, fields
from openerp.osv.expression import get_unaccent_wrapper
from openerp.tools.translate import _

class sales_manager(osv.osv):
    
    _name = "sales.manager"  
      
    _columns = {
                'name':fields.char('Name'),
                'branch_ids':fields.many2many('res.branch','sales_manager_branch_rel', 'sales_manager_id', 'branch_id', string='Branch'),
                'sales_team_line_ids':fields.one2many('crm.case.section', 'sales_manager_id', string='Sales Teams'),
                'active':fields.boolean('Active' , default=True),   
            }     
