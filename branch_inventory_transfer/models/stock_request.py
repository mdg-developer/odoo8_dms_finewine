'''
Created on Auguest 31, 2016

@author: Administrator
'''
import time

import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser
import time
from openerp.osv import fields , osv
from openerp.tools.translate import _
import datetime
import math
from datetime import datetime, date, time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATETIMEFORMAT
import openerp.addons.decimal_precision as dp


class branch_stock_requisition(osv.osv):
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _name = "branch.stock.requisition"
    _description = "Branch Stock Requisition"
    _order = "id desc"    
    _track = {
        'state': {
            'branch_stock_requisition.mt_requisition_confirm': lambda self, cr, uid, obj, ctx = None: obj.state in ['confirm'],
            'branch_stock_requisition.mt_requisition_approve': lambda self, cr, uid, obj, ctx = None: obj.state in ['approve']
        },
    }        

    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        if not company_id:
            raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))
        return company_id     
    
    def on_change_branch_id(self, cr, uid, ids, branch_id, context=None):
        values = {}
        domain={}

        if branch_id:
            branch_data = self.pool.get('res.branch').browse(cr, uid, branch_id, context=context)
            branch_location = branch_data.branch_location_id.id
            cr.execute("""select location_id from branch_request_line
                          WHERE request_id = %s""", (branch_data.id,))
            location_list = cr.fetchall()
            cr.execute("""select location_id from branch_requesting_line
                          WHERE requesting_id = %s""", (branch_data.id,))
            to_location_list = cr.fetchall()
            domain = {'from_location_id':
                        [('id', 'in', location_list)],
                        'to_location_id':
                        [('id', 'in', to_location_list)]}

            values = {
                 'from_location_id':branch_location,
            }
        return {'value': values, 'domain': domain}    

    def _viss_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            for line in order.p_line:
                req_data = self.pool.get('branch.stock.requisition.line').browse(cr, uid, line.id, context=context)
                val1 += req_data.viss_value                      
            res[order.id] = val1
        return res            

    def _cbm_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            for line in order.p_line:
                req_data = self.pool.get('branch.stock.requisition.line').browse(cr, uid, line.id, context=context)
                val1 += req_data.cbm_value                      
            res[order.id] = val1
        return res   
       
    def _total_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            for line in order.p_line:
                req_data = self.pool.get('branch.stock.requisition.line').browse(cr, uid, line.id, context=context)
                val1 += req_data.product_value                      
            res[order.id] = val1
        return res        
    
    def _bal_cbm_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            val1 = order.max_viss - order.total_viss                      
            res[order.id] = val1
        return res     

    def _bal_viss_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            val1 = order.max_cbm - order.total_cbm                      
            res[order.id] = val1
        return res                    
    
    def on_change_vehicle_id(self, cr, uid, ids, vehicle_id, context=None):
        values = {}

        if vehicle_id:
            vehicle_data = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)
            viss = vehicle_data.weight_viss
            cbm = vehicle_data.vol_cbm

            values = {
                 'max_viss':viss, 'max_cbm':cbm,
            }
        return {'value': values}    
    
    def on_change_truck_id(self, cr, uid, ids, truck_id, context=None):
        values = {}

        if truck_id:
            truck_data = self.pool.get('truck.type').browse(cr, uid, truck_id, context=context)
            viss = truck_data.est_viss
            cbm = truck_data.est_cbm

            values = {
                 'max_viss':viss, 'max_cbm':cbm,
            }
        return {'value': values} 
       
    _columns = {
        'branch_id': fields.many2one('res.branch', 'Branch', required=True),
        'name': fields.char('BRFI Ref', readonly=True),
        'from_location_id':fields.many2one('stock.location', 'Requesting  Location', readonly=False),
        'to_location_id':fields.many2one('stock.location', 'Request Warehouse' , required=False),
        # 'so_no' : fields.char('Sales Order/Inv Ref;No.'),
        'issue_to':fields.char("Receiver"),
        'request_by':fields.many2one('res.users', "Requested By" , readonly=True),
        'approve_by':fields.many2one('res.users', "Approved By", readonly=True),
        'request_date' : fields.date('Date Requested'),
        'vehicle_id':fields.many2one('fleet.vehicle', 'Vehicle No'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
            ('approve', 'Open'),
            ('partial', 'Partial'),
            ('done', 'Done'),
            ('complete_partial', 'Complete Partial'),
            ('cancel', 'Cancel'),
            ], 'Status', readonly=True, copy=False, help="Gives the status of the quotation or sales order.\
              \nThe exception status is automatically set when a cancel operation occurs \
              in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
               but waiting for the scheduler to run on the order date.", select=True),
        'p_line':fields.one2many('branch.stock.requisition.line', 'line_id', 'Product Lines',
                              copy=True),
    'company_id':fields.many2one('res.company', 'Company'),
    'truck_type_id': fields.many2one('truck.type', 'Truck Type'),
    'max_viss': fields.float(string='Max CBM', digits=(16, 2)),
    'max_cbm': fields.float(string='Max Viss', digits=(16, 2)),
    'total_viss':fields.function(_viss_amount, string='Total Viss', digits_compute=dp.get_precision('Product Price'), type='float'),
    'total_cbm':fields.function(_cbm_amount, string='Total CBM', digits_compute=dp.get_precision('Product Price'), type='float'),
    'bal_viss':fields.function(_bal_cbm_amount, string='Bal Viss', digits_compute=dp.get_precision('Product Price'), type='float'),
    'bal_cbm':fields.function(_bal_viss_amount, string='Bal CBM', digits_compute=dp.get_precision('Product Price'), type='float'),
    'total_value':fields.function(_total_value, string='Total Value', digits_compute=dp.get_precision('Product Price'), type='float'),
   'pricelist_id': fields.many2one('product.pricelist', 'Price list', required=True , readonly=True),

}
    _defaults = {
        'state' : 'draft',
         'company_id': _get_default_company,
         'request_date': fields.datetime.now,
         'request_by':lambda obj, cr, uid, context: uid,
         'pricelist_id':1,
         
    }     
    
    def create(self, cursor, user, vals, context=None):       
        id_code = self.pool.get('ir.sequence').get(cursor, user,
                                                'branch.request.code') or '/'
        vals['name'] = id_code
        # vals['from_location_id'] = from_location_id
        
        return super(branch_stock_requisition, self).create(cursor, user, vals, context=context)
 
    def approve(self, cr, uid, ids, context=None):
        # , 'good_issue_id':good_id
        return self.write(cr, uid, ids, {'state':'approve' , 'approve_by':uid})    
    
    def confirm(self, cr, uid, ids, context=None):
        # , 'good_issue_id':good_id
        return self.write(cr, uid, ids, {'state':'confirm' })        
    
    def cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'cancel' })    

    def retrieve_data(self, cr, uid, ids, context=None):
        branch_req_line_obj = self.pool.get('branch.stock.requisition.line')
        branch_obj = self.pool.get('res.branch')
        request_data = self.browse(cr, uid, ids, context=context)
        branch_id = request_data.branch_id.id
        to_location_id = request_data.to_location_id
        pricelist_id = request_data.pricelist_id.id
        branch_data = branch_obj.browse(cr, uid, branch_id, context=context)
        cr.execute('delete from branch_stock_requisition_line where line_id=%s', (ids[0],))
        for b_data in branch_data.p_line:
            if b_data.assign == True:
                product_id = b_data.product_id.id  
                product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
                cr.execute('select  SUM(COALESCE(qty,0)) qty from stock_quant where location_id=%s and product_id=%s and qty >0 group by product_id', (to_location_id.id, product.id,))
                qty_on_hand = cr.fetchone()
                if qty_on_hand:
                    qty_on_hand = qty_on_hand[0]
                else:
                    qty_on_hand = 0 
                print 'productname', product.name_template
                cr.execute("select new_price from product_pricelist_item where price_version_id in ( select id from product_pricelist_version where pricelist_id=%s) and product_id=%s and product_uom_id=%s", (pricelist_id, product.id, product.report_uom_id.id,))
                product_price = cr.fetchone()[0]                
                branch_req_line_obj.create(cr, uid, {'line_id': ids[0],
                               'sequence':product.sequence,
                              'product_id': product_id,
                              'product_uom':product.report_uom_id.id,
                              'qty_on_hand':qty_on_hand,
                              'viss_value':product.viss_value,
                              'cbm_value':product.cbm_value,
                              'product_value':product_price,
                        }, context=context)  

                
class stock_requisition_line(osv.osv):  # #prod_pricelist_update_line
    _name = 'branch.stock.requisition.line'
    _description = 'Request Line'
    
    def create(self, cr, uid, data, context=None):
        requisition_obj = self.pool.get('branch.stock.requisition')
        line_id = data['line_id']
        line_ids = requisition_obj.search(cr, uid, [('id', '=', line_id)], context=context)
        requisition = requisition_obj.browse(cr, uid, line_ids, context)
        location_id = requisition.to_location_id.id
        product = data['product_id']
        product_data = self.pool.get('product.product').browse(cr, uid, product, context=context)
        cr.execute('select  SUM(COALESCE(qty,0)) qty from stock_quant where location_id=%s and product_id=%s and qty >0 group by product_id', (location_id, product,))
        qty_on_hand = cr.fetchone()
        if qty_on_hand:
            qty_on_hand = qty_on_hand[0]
        else:
            qty_on_hand = 0
        data['qty_on_hand'] = qty_on_hand
        # comment by EMTW
        data['product_uom'] = product_data.product_tmpl_id.report_uom_id.id
        return super(stock_requisition_line, self).create(cr, uid, data, context=context)
    
    def on_change_product_id(self, cr, uid, ids, product_id, to_location_id, context=None):
        values = {}
        domain = {}
        qty_on_hand = 0
        if to_location_id and product_id:
            cr.execute('select  SUM(COALESCE(qty,0)) qty from stock_quant where location_id=%s and product_id=%s and qty >0 group by product_id', (to_location_id, product_id,))
            qty_on_hand = cr.fetchone()
            if qty_on_hand:
                qty_on_hand = qty_on_hand[0]
            else:
                qty_on_hand = 0
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            values = {
                'product_uom': product.product_tmpl_id.report_uom_id and product.product_tmpl_id.report_uom_id.id or False,
                'qty_on_hand':qty_on_hand,
                'sequence':product.sequence,
            }
            cr.execute("""SELECT uom.id FROM product_product pp 
                          LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                          LEFT JOIN product_template_product_uom_rel rel ON (rel.product_template_id=pt.id)
                          LEFT JOIN product_uom uom ON (rel.product_uom_id=uom.id)
                          WHERE pp.id = %s""", (product.id,))
            uom_list = cr.fetchall()
            domain = {'product_uom': [('id', 'in', uom_list)]}
            
        return {'value': values, 'domain':domain}
    
    def _diff_quantity_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            

            val1 = order.req_quantity - order.issue_quantity                      
            res[order.id] = val1
        return res           
    
    _columns = {                
        'line_id':fields.many2one('branch.stock.requisition', 'Line', ondelete='cascade', select=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'req_quantity' : fields.float(string='Request (Qty)', digits=(16, 0)),
        'issue_quantity': fields.float(string='Issued (Qty)', digits=(16, 0)),
        'diff_quantity':fields.function(_diff_quantity_value, string='Diff(Qty)', digits=(16, 0), type='float', readonly=True),
        'loss' : fields.boolean(string='Loose'),
        'product_value' : fields.float(string='Value', digits=(16, 0)),
        'viss_value' : fields.float(string='Viss', digits=(16, 0)),
        'cbm_value' : fields.float(string='CBM', digits=(16, 0)),
        'product_uom': fields.many2one('product.uom', ' UOM'),
        'uom_ratio':fields.char('Packing Unit'),
         'remark':fields.char('Remark'),
        'qty_on_hand':fields.float(string='Qty On Hand', digits=(16, 0)),
        'sequence':fields.integer('Sequence'),
    }
  