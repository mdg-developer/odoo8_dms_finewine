from openerp.osv import fields, osv
from openerp.tools.translate import _

class customer_asset(osv.osv):
    _inherit = "res.partner.asset"
    
    def _get_default_branch(self, cr, uid, context=None):
        branch_id = self.pool.get('res.users')._get_branch(cr, uid, context=context)
        if not branch_id:
            raise osv.except_osv(_('Error!'), _('There is no default branch for the current user!'))
        return branch_id
        
    _columns = {
               'branch_id':fields.many2one('res.branch', 'Branch'),
               }
    _defaults = {
        'branch_id': _get_default_branch,
        }