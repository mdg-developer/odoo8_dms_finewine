from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class branch_good_issue_note(osv.osv):    
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _name = "branch.good.issue.note"
    
    def _get_tcl_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        tcl_value = 0
        if context is None:
            context = {}
            
        for gin in self.browse(cr, uid, ids, context=context):
            gin_data = self.browse(cr, uid, gin.id, context=context)
            if gin_data:
                if  gin_data.total_value != 0:         
                    tcl_value = (gin_data.total_tcl / gin_data.total_value) * 100
                                 
            res[gin_data.id] = tcl_value            
        return res     
    
    def _get_total_tcl(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        total_tcl = 0.0
        if context is None:
            context = {}
            
        for gin in self.browse(cr, uid, ids, context=context):
            gin_data = self.browse(cr, uid, gin.id, context=context)
            if gin_data:         
                total_tcl = gin_data.labor_cost + gin_data.transport_cost
             
            res[gin_data.id] = total_tcl            
        return res     
        
    def _get_total_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        total_value = 0.0
        if context is None:
            context = {}       
                        
        for gin in self.browse(cr, uid, ids, context=context):
            gin_data = self.browse(cr, uid, gin.id, context=context)
            if gin_data:
                for line in gin_data.p_line:
                    total_value = total_value + line.product_value
            res[gin_data.id] = total_value            
        return res   

    def _viss_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            for line in order.p_line:
                req_data = self.pool.get('branch.good.issue.note.line').browse(cr, uid, line.id, context=context)
                val1 += req_data.product_viss                     
            res[order.id] = val1
        return res            

    def _cbm_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            for line in order.p_line:
                req_data = self.pool.get('branch.good.issue.note.line').browse(cr, uid, line.id, context=context)
                val1 += req_data.product_cbm                      
            res[order.id] = val1
        return res       
    
    def _bal_cbm_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0  
            val1 = order.max_cbm - order.total_cbm                             
            res[order.id] = val1
        return res     

    def _bal_viss_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            val1 = order.max_weight - order.total_viss                                                 
            res[order.id] = val1
        return res           
    
    def change_location(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'branch_inventory_transfer', 'view_change_diff_location')
        inv = self.browse(cr, uid, ids[0], context=context)
        return {
            'name':_("Change Location"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'change.diff.location',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
            'default_from_location_id': inv.transit_location.id,
            'default_note_id':inv.id,
            }
        }    

    _columns = {
        'name': fields.char('GIN Ref', readonly=True),
        'grn_no':fields.char('GRN Ref', readonly=True),
        'branch_id':fields.many2one('res.branch', 'Branch', required=True),
        'to_location_id':fields.many2one('stock.location', 'Requesting Location', readonly=True, required=True),
        'request_by':fields.many2one('res.users', "Requested By", readonly=True),
        'issue_date':fields.date('Date for Issue', required=True),
        'receive_date':fields.date('Date for Receive', required=False),
        'request_id':fields.many2one('branch.stock.requisition', 'RFI Ref', readonly=True),
        'from_location_id':fields.many2one('stock.location', 'Request Warehouse', readonly=True, required=True),
        'supplier_id': fields.many2one('res.partner', 'Supplier'),
        'vehicle_id': fields.many2one('fleet.vehicle', 'Vehicle'),
        'route_id': fields.many2one('transport.route', 'Route'),
        'max_weight':fields.related('vehicle_id', 'alert_weight_viss', type='float', store=False, string='Max Viss'),
        'max_cbm':fields.related('vehicle_id', 'alert_vol_cbm', type='float', store=False, string='Max CBM'),
        'is_changed': fields.boolean('Is Changed'),
        'approve_by':fields.many2one('res.users', "Approved By"),
        'pricelist_id': fields.many2one('product.pricelist', 'Price list', required=True, readonly=True),
        'issue_by':fields.char("Issuer"),
        'receiver':fields.char("Receiver"),
        'loading_date' : fields.date('Loading Date'),
        'eta_date' : fields.date('ETA Date'),
        'variable_costing': fields.boolean('Is Variable Costing'),
        'transport_cost': fields.float('Transport Cost'),
        'labor_cost': fields.float('Labor Cost'),
        'total_value': fields.function(_get_total_value, type='float', string='Total Value'),
        'total_tcl': fields.function(_get_total_tcl, type='float', string='Total TCL'),
        'transit_location':fields.many2one('stock.location', "Transit Location"),
        'total_tcl': fields.function(_get_total_tcl, type='float', string='Total TCL'),
        'tcl_value': fields.function(_get_tcl_value, type='float', string='TCL/Value(%)'),
        'p_line':fields.one2many('branch.good.issue.note.line', 'line_id', 'Product Lines',
                              copy=True),
        'state': fields.selection([
            ('pending', 'Pending'),
            ('approve', 'Approved'),
            ('issue', 'Issued'),
            ('receive', 'Received'),
            ('cancel', 'Cancel'),
            ], 'Status', readonly=True, copy=False, help="Gives the status of the quotation or sales order.\
              \nThe exception status is automatically set when a cancel operation occurs \
              in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
               but waiting for the scheduler to run on the order date.", select=True),
    'total_viss':fields.function(_viss_amount, string='Total Viss', digits_compute=dp.get_precision('Product Price'), type='float'),
    'total_cbm':fields.function(_cbm_amount, string='Total CBM', digits_compute=dp.get_precision('Product Price'), type='float'),
    'bal_viss':fields.function(_bal_cbm_amount, string='Bal Viss', digits_compute=dp.get_precision('Product Price'), type='float'),
    'bal_cbm':fields.function(_bal_viss_amount, string='Bal CBM', digits_compute=dp.get_precision('Product Price'), type='float'),
        }
    
    _defaults = {
         'state' : 'pending',
         'request_date': fields.datetime.now,
         'request_by':lambda obj, cr, uid, context: uid,
         'pricelist_id':1,
         
    }
    
    def create(self, cursor, user, vals, context=None):       
        id_code = self.pool.get('ir.sequence').get(cursor, user,
                                                'branch.gin.code') or '/'
        vals['name'] = id_code       
        return super(branch_good_issue_note, self).create(cursor, user, vals, context=context)
    
    def approve(self, cr, uid, ids, context=None):
        if ids:
            request_data=self.browse(cr, uid, ids[0], context=context)
            max_cbm=request_data.max_cbm
            total_cbm=request_data.total_cbm
            max_viss=request_data.max_weight
            total_viss=request_data.total_cbm
            if total_viss > max_viss and total_cbm >max_cbm:
                    raise osv.except_osv(
                        _('Warning!'),
                        _('Please Check Your CBM and Viss Value.It is Over!')
                    )         
        return self.write(cr, uid, ids, {'state': 'approve', 'approve_by':uid})   
    
    def issue(self, cr, uid, ids, context=None):
        product_line_obj = self.pool.get('branch.good.issue.note.line')
        note_obj = self.pool.get('branch.good.issue.note')
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        note_value = req_lines = {}
        if ids:
            note_value = note_obj.browse(cr, uid, ids[0], context=context)
            issue_date = note_value.issue_date
            # location_id = note_value.tansit_location.id
            location_id = note_value.to_location_id.id
            from_location_id = note_value.transit_location.id
            origin = note_value.name
            cr.execute('select id from stock_picking_type where default_location_dest_id=%s and name like %s', (location_id, '%Internal Transfer%',))
            price_rec = cr.fetchone()
            if price_rec: 
                picking_type_id = price_rec[0] 
            else:
                raise osv.except_osv(_('Warning'),
                                     _('Picking Type has not for this transition'))
            picking_id = picking_obj.create(cr, uid, {
                                          'date': issue_date,
                                          'origin':origin,
                                          'picking_type_id':picking_type_id}, context=context)
            note_line_id = product_line_obj.search(cr, uid, [('line_id', '=', ids[0])], context=context)
            if note_line_id and picking_id:
                for note_id in note_value.p_line:
                    note_line_value = product_line_obj.browse(cr, uid, note_id.id, context=context)
                    product_id = note_line_value.product_id.id
                    name = note_line_value.product_id.name_template
                    product_uom = note_line_value.product_uom.id
                    origin = origin
                    quantity = note_line_value.issue_quantity                        
                    move_id = move_obj.create(cr, uid, {'picking_id': picking_id,
                                              'picking_type_id':picking_type_id,
                                          'product_id': product_id,
                                          'product_uom_qty': quantity,
                                          'product_uos_qty': quantity,
                                          'product_uom':product_uom,
                                          'location_id':location_id,
                                          'location_dest_id':from_location_id,
                                          'name':name,
                                           'origin':origin,
                                          'state':'confirmed'}, context=context)     
                    move_obj.action_done(cr, uid, move_id, context=context)  
                    cr.execute('''update stock_move set date=((%s::date)::text || ' ' || date::time(0))::timestamp where state='done' and origin =%s''', (issue_date, origin,))
        return self.write(cr, uid, ids, {'state': 'issue'})       

    def receive(self, cr, uid, ids, context=None):
        product_line_obj = self.pool.get('branch.good.issue.note.line')
        note_obj = self.pool.get('branch.good.issue.note')
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        note_value = req_lines = {}
        grn_code = self.pool.get('ir.sequence').get(cr, uid,
                                                'branch.grn.code') or '/'    
        if ids:
            note_value = note_obj.browse(cr, uid, ids[0], context=context)
            receive_date = note_value.receive_date
            if not receive_date:
                raise osv.except_osv(_('Warning'),
                         _('Please Insert Receive Date'))
            # location_id = note_value.tansit_location.id
            location_id = note_value.transit_location.id
            from_location_id = note_value.from_location_id.id
            origin = grn_code
            cr.execute('select id from stock_picking_type where default_location_dest_id=%s and name like %s', (from_location_id, '%Internal Transfer%',))
            price_rec = cr.fetchone()
            if price_rec: 
                picking_type_id = price_rec[0] 
            else:
                raise osv.except_osv(_('Warning'),
                                     _('Picking Type has not for this transition'))
            picking_id = picking_obj.create(cr, uid, {
                                          'date': receive_date,
                                          'origin':origin,
                                          'picking_type_id':picking_type_id}, context=context)
            note_line_id = product_line_obj.search(cr, uid, [('line_id', '=', ids[0])], context=context)
            if note_line_id and picking_id:
                for note_id in note_value.p_line:
                    note_line_value = product_line_obj.browse(cr, uid, note_id.id, context=context)
                    product_id = note_line_value.product_id.id
                    name = note_line_value.product_id.name_template
                    product_uom = note_line_value.product_uom.id
                    origin = origin
                    quantity = note_line_value.receive_quantity                        
                    move_id = move_obj.create(cr, uid, {'picking_id': picking_id,
                                              'picking_type_id':picking_type_id,
                                          'product_id': product_id,
                                          'product_uom_qty': quantity,
                                          'product_uos_qty': quantity,
                                          'product_uom':product_uom,
                                          'location_id':location_id,
                                          'location_dest_id':from_location_id,
                                          'name':name,
                                           'origin':origin,
                                          'state':'confirmed'}, context=context)     
                    move_obj.action_done(cr, uid, move_id, context=context)  
                    cr.execute('''update stock_move set date=((%s::date)::text || ' ' || date::time(0))::timestamp where state='done' and origin =%s''', (receive_date, origin,))
    
        return self.write(cr, uid, ids, {'state': 'receive', 'grn_no':grn_code}) 
    
    def transfer_other_location(self, cr, uid, ids, from_location_id, to_location_id, date, context=None):
        product_line_obj = self.pool.get('branch.good.issue.note.line')
        note_obj = self.pool.get('branch.good.issue.note')
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        note_value = req_lines = {}
        if ids:
            note_value = note_obj.browse(cr, uid, ids, context=context)
            receive_date = note_value.receive_date
            if not receive_date:
                raise osv.except_osv(_('Warning'),
                         _('Please Insert Receive Date'))
            # location_id = note_value.tansit_location.id
            location_id = from_location_id
            from_location_id = to_location_id
            origin = 'CHANGE ' + note_value.name
            cr.execute('select id from stock_picking_type where default_location_dest_id=%s and name like %s', (from_location_id, '%Internal Transfer%',))
            price_rec = cr.fetchone()
            if price_rec: 
                picking_type_id = price_rec[0] 
            else:
                raise osv.except_osv(_('Warning'),
                                     _('Picking Type has not for this transition'))
            picking_id = picking_obj.create(cr, uid, {
                                          'date': receive_date,
                                          'origin':origin,
                                          'picking_type_id':picking_type_id}, context=context)
#             note_line_id = product_line_obj.search(cr, uid, [('line_id', '=', ids[0])], context=context)
#             if note_line_id and picking_id:
            for note_id in note_value.p_line:
                note_line_value = product_line_obj.browse(cr, uid, note_id.id, context=context)
                product_id = note_line_value.product_id.id
                name = note_line_value.product_id.name_template
                product_uom = note_line_value.product_uom.id
                origin = origin
                quantity = note_line_value.diff_quantity      
                if quantity > 0:             
                    move_id = move_obj.create(cr, uid, {'picking_id': picking_id,
                                              'picking_type_id':picking_type_id,
                                          'product_id': product_id,
                                          'product_uom_qty': quantity,
                                          'product_uos_qty': quantity,
                                          'product_uom':product_uom,
                                          'location_id':location_id,
                                          'location_dest_id':from_location_id,
                                          'name':name,
                                           'origin':origin,
                                          'state':'confirmed'}, context=context)     
                    move_obj.action_done(cr, uid, move_id, context=context)  
            cr.execute('''update stock_move set date=((%s::date)::text || ' ' || date::time(0))::timestamp where state='done' and origin =%s''', (receive_date, origin,))
        return self.write(cr, uid, ids, {'state': 'receive', 'is_changed':True}) 
        
    def onchange_vehicle(self, cr, uid, ids, vehicle_id, context=None):  
        if vehicle_id:
            vehicle = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)                       
            route_id = self.pool.get('transport.route.line').search(cr, uid, [('vehicle_id', '=', vehicle_id)], context=context)
            route_obj = self.pool.get('transport.route.line').browse(cr, uid, route_id, context=context) 
            if route_id:                    
                return {'value' : {'max_weight' : vehicle.alert_weight_viss, 'max_cbm' : vehicle.alert_vol_cbm,
                               'supplier_id':vehicle.supplier_id, 'transport_cost' :route_obj.transport_cost, 'labor_cost' : route_obj.labor_cost, }}

    def onchange_route(self, cr, uid, ids, route_id, context=None):
        domain = {}

        if route_id:
            route_ids = self.pool.get('transport.route.line').search(cr, uid, [('line_id', '=', route_id)], context=context)
            route_list = str(tuple(route_ids))
            route_list = eval(route_list)
            cr.execute('SELECT vehicle_id  FROM transport_route_line where id in %s', (route_list,))
            vehicle_list = cr.fetchall()
            if vehicle_list:        
                domain = {'vehicle_id': [('id', 'in', vehicle_list)]}
        return {'domain':domain}           

      
class branch_good_issue_note_line(osv.osv):  
    _name = 'branch.good.issue.note.line'
    
    def _diff_quantity_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            

            val1 = order.issue_quantity - order.receive_quantity                      
            res[order.id] = val1
        return res               

    def on_change_product_id(self, cr, uid, ids, product_id, context=None):
        values = {}
        domain = {}

        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            values = {
                'product_uom': product.product_tmpl_id.report_uom_id and product.product_tmpl_id.report_uom_id.id or False,
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
    
    def _cal_viss_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        uom_ratio = 1
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            product = self.pool.get('product.product').browse(cr, uid, order.product_id.id, context=context)
            if product.product_tmpl_id.uom_id.id == order.product_uom.id:
                uom_ratio = product.product_tmpl_id.report_uom_id.factor            
            if order.issue_quantity > 0:
                val1 = order.issue_quantity * (product.viss_value / uom_ratio)
            else:
                val1 = product.viss_value                                     
            res[order.id] = val1
        return res       
    
    def _cal_cbm_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        uom_ratio = 1
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            product = self.pool.get('product.product').browse(cr, uid, order.product_id.id, context=context)
            if product.product_tmpl_id.uom_id.id == order.product_uom.id:
                uom_ratio = product.product_tmpl_id.report_uom_id.factor
                
            if order.issue_quantity > 0:
                val1 = order.issue_quantity * (product.cbm_value / uom_ratio)      
            else:
                val1 = product.cbm_value      
            res[order.id] = val1
        return res     

    def _cal_product_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            request_data = self.pool.get('branch.good.issue.note').browse(cr, uid, order.line_id.id, context=context)
            if request_data:
                pricelist_id = request_data.pricelist_id.id
                cr.execute("select new_price from product_pricelist_item where price_version_id in ( select id from product_pricelist_version where pricelist_id=%s) and product_id=%s and product_uom_id=%s", (pricelist_id, order.product_id.id, order.product_uom.id,))
                product_price = cr.fetchone()
                if product_price:
                    product_value = product_price[0]  
                else:
                    product_value = 0           
                if order.issue_quantity > 0:
                    val1 = order.issue_quantity * product_value      
                else:
                    val1 = product_price     
                res[order.id] = val1
        return res          

    _columns = {                
        'line_id':fields.many2one('branch.good.issue.note', 'Line', ondelete='cascade', select=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'issue_quantity': fields.float(string='Issued (Qty)', digits=(16, 0), readonly=False),
        'receive_quantity' : fields.float(string='Received (Qty)', digits=(16, 0)),
        'diff_quantity':fields.function(_diff_quantity_value, string='Diff(Qty)', digits=(16, 0), type='float', readonly=True),
        'product_uom': fields.many2one('product.uom', ' UOM'),
        'qty_on_hand':fields.float(string='Qty On Hand(S)', digits=(16, 0)),
        'sequence':fields.integer('Sequence'),
        'product_value':fields.function(_cal_product_value, string='Value', digits=(16, 0), type='float'),
        'product_loss' : fields.boolean(string='Loose'),
#         'product_viss' : fields.float(string='Viss', digits=(16, 0)),
#         'product_cbm' : fields.float(string='CBM', digits=(16, 0)),
        'product_viss':fields.function(_cal_viss_value, string='Viss', digits_compute=dp.get_precision('Product Price'), type='float'),
        'product_cbm':fields.function(_cal_cbm_value, string='CBM', digits_compute=dp.get_precision('Product Price'), type='float'),
         'remark':fields.char('Remark'),
        'state':fields.related('line_id', 'state', type='char', store=False, string='State'),
    }
    
