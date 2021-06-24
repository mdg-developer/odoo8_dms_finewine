from openerp.osv import fields, osv
import xmlrpclib

class branch_stock_requisition(osv.osv):
    _inherit = "branch.stock.requisition"
    
    def approve(self, cr, uid, ids, context=None):
        try:
            order_id = False
            result = super(branch_stock_requisition, self).approve(cr, uid, ids, context=context)
            product_line_obj = self.pool.get('branch.stock.requisition.line')
            requisition_obj = self.pool.get('branch.stock.requisition')
            good_obj = self.pool.get('branch.good.issue.note')
            branch_obj = self.pool.get('res.branch')
            good_line_obj = self.pool.get('branch.good.issue.note.line')
            
            sd_uid,url,db,password = self.pool['cwh.connection'].get_connection_data(cr, uid, context=None)
            models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
            so_vals={}
            so_vals['partner_id'] =7                         
            so_vals['order_line']= []   
            if ids:
                req_value = requisition_obj.browse(cr, uid, ids[0], context=context)
                so_vals['client_order_ref']= req_value.from_location_id.name or ''
                so_create = False
                for req_line_id in req_value.p_line:
                    request_line_data=product_line_obj.browse(cr, uid, req_line_id.id, context=context)
                    if request_line_data.req_quantity>0: 
                        
                        product_ids = models.execute_kw(
                        db, sd_uid, password,
                        'product.product', 'search',
                        [[('default_code', '=',request_line_data.product_id.default_code)]],
                        {'limit': 1})
                        if product_ids:
                            loose = False
                            if request_line_data.loss == True:
                                route_id = models.execute_kw(
                                db, sd_uid, password,
                                'stock.location.route', 'search',
                                [[('pickface_pcs_route', '=', True),('active','=',True)]],
                                {'limit': 1})
                                if route_id:
                                    loose =route_id[0]
                            so_create = True
                            uom_id = False
                            #product_id=models.execute_kw(db, sd_uid, password, 'product.product', 'read', [product_ids])[0]
                            product_id=models.execute_kw(db, sd_uid, password, 'product.product', 'read', [product_ids])[0]
                            uom_id=models.execute_kw(db, sd_uid, password, 'uom.uom', 'search',  [[('name', '=',request_line_data.product_uom.name)]],
                                                         {'limit': 1})
                            print 'product_id', product_id
                            print 'uom_id', uom_id[0]
                            so_vals['order_line'].append([0, False, {'name': request_line_data.product_id.name, 'product_id': product_id['id'],
                                'product_uom_qty': request_line_data.req_quantity, 'product_uom': uom_id[0],'price_unit':product_id['lst_price'],
                                'loose':loose
                                }])
                if so_create == True:
                    order_id = models.execute_kw(db, sd_uid, password, 'sale.order', 'create', [so_vals])
                    if order_id:
                        print 'order_id', order_id
                        models.execute_kw(db, sd_uid, password, 'sale.order', 'action_confirm', [order_id])
        except Exception , e:
            print "error order id",order_id
            if order_id:
                models.execute_kw(db, sd_uid, password, 'sale.order', 'unlink', [[order_id]])
            raise e            
            
                      