from openerp.osv import fields, osv

class product_department(osv.osv):
    _name = "product.department"
    _columns = {
        'name': fields.char('Name'),
    }

product_department()