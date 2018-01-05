from openerp.osv import fields, osv
from openerp.osv import orm
from datetime import datetime
from openerp.tools.translate import _
import ast
import time
from openerp import netsvc
DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"

class customer_payment(osv.osv):
    _name = "customer.payment"
    _columns = {               
   'payment_id':fields.many2one('mobile.sale.order', 'Line'),
   'pre_order_id'  :fields.many2one('pre.sale.order', 'Line'),
   'journal_id'  : fields.many2one('account.journal', 'Payment Method' , domain=[('type', 'in', ('cash', 'bank'))]),
   'amount':fields.float('Paid Amount'),
   'notes':fields.char('Payment Ref'),
   'date':fields.date('Date'),
   'cheque_no':fields.char('Cheque No'),
   'partner_id':fields.many2one('res.partner', 'Customer'),
   'sale_team_id':fields.many2one('crm.case.section', 'Sale Team'),
   'payment_code':fields.char('Payment Code'),
        }
    
class mobile_sale_order(osv.osv):
    
    _name = "mobile.sale.order"
    _description = "Mobile Sales Order"
   
    _columns = {
        'name': fields.char('Order Reference', size=64),
        'partner_id':fields.many2one('res.partner', 'Customer'),
        'customer_code':fields.char('Customer Code'),
        'outlet_type':fields.many2one('outlettype.outlettype', 'Outlet Type'),
        'user_id':fields.many2one('res.users', 'Salesman Name'),
        'sale_plan_name':fields.char('Sale Plan Name'),
        'mso_latitude':fields.float('Geo Latitude'),
        'mso_longitude':fields.float('Geo Longitude'),
        'amount_total':fields.float('Total Amount'),
        'type':fields.selection([
                ('credit', 'Credit'),
                ('cash', 'Cash'),
                ('consignment', 'Consignment'),
                ('advanced', 'Advanced')
            ], 'Payment Type'),
        'delivery_remark':fields.selection([
                ('partial', 'Partial'),
                ('delivered', 'Delivered'),
                ('none', 'None')
            ], 'Deliver Remark'),
        'additional_discount':fields.float('Discount'),
        'deduction_amount':fields.float('Deduction Amount'),
        'net_amount':fields.float('Net Amount'),
        'change_amount':fields.float('Change Amount'),
        'remaining_amount':fields.float('Remaining Amount'),
        'balance':fields.float('Balance'),
        'paid_amount':fields.float('Paid Amount'),
        'paid':fields.boolean('Paid'),
        'void_flag':fields.selection([
                ('voided', 'Voided'),
                ('none', 'Unvoid')
            ], 'Void'),
        'date':fields.datetime('Date'),
        'note':fields.text('Note'),
        'order_line': fields.one2many('mobile.sale.order.line', 'order_id', 'Order Lines', copy=True),
        'delivery_order_line': fields.one2many('products.to.deliver', 'sale_order_id', 'Delivery Order Lines', copy=True),
        'tablet_id':fields.many2one('tablets.information', 'Tablet ID'),
        'sale_plan_day_id':fields.many2one('sale.plan.day', 'Sale Plan Day'),
        'sale_plan_trip_id':fields.many2one('sale.plan.trip', 'Sale Plan Trip'),
        'warehouse_id' : fields.many2one('stock.warehouse', 'Warehouse'),
        'sale_team':fields.many2one('crm.case.section', 'Sale Team'),
        'location_id'  : fields.many2one('stock.location', 'Location'),
        'm_status':fields.selection([('draft', 'Draft'),
                                                      ('done', 'Complete')], string='Status'),
        'due_date':fields.date('Due Date'),
        'payment_term': fields.many2one('account.payment.term', 'Payment Term'),
       'promos_line_ids':fields.one2many('mso.promotion.line', 'promo_line_id', 'Promotion Lines'),
       'pricelist_id': fields.many2one('product.pricelist', 'Price List', select=True, ondelete='cascade'),
       'payment_line_ids':fields.one2many('customer.payment', 'payment_id', 'Payment Lines'),
      'branch_id': fields.many2one('res.branch', 'Branch', required=True),
      
   #     'journal_id'  : fields.many2one('account.journal', 'Journal' ,domain=[('type','in',('cash','bank'))]),   
    }
    _order = 'id desc'
    _defaults = {
        'date': datetime.now(),
        'm_status' : 'draft',
       
    } 
    
    def create_massive(self, cursor, user, vals, context=None):
        print 'vals', vals
        sale_order_name_list = []
        try : 
            mobile_sale_order_obj = self.pool.get('mobile.sale.order')
            mobile_sale_order_line_obj = self.pool.get('mobile.sale.order.line')
            str = "{" + vals + "}"
            str = str.replace(":''", ":'")  # change Order_id
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            sale_order = []
            sale_order_line = []
            for r in result:
                print "length", len(r)
                if len(r) >= 28:
                    sale_order.append(r)
                else:
                    sale_order_line.append(r)
            
            if sale_order:
                for so in sale_order:
                    cursor.execute('select branch_id from crm_case_section where id=%s', (so['sale_team'],))
                    branch_id = cursor.fetchone()[0]     
                    cursor.execute('select id From res_partner where customer_code  = %s ', (so['customer_code'],))
                    data = cursor.fetchall()                
                    if data:
                        partner_id = data[0][0]
                    else:
                        partner_id = None 
                        
                    if so['type'] == 'cash':
                        paid = True
                    else:
                        paid = False
                        
                    mso_result = {
                        'customer_code':so['customer_code'],
                        'sale_plan_day_id':so['sale_plan_day_id'],
                        'sale_plan_trip_id':so['sale_plan_trip_id'] ,
                        'paid': paid,
                        'warehouse_id':so['warehouse_id'],
                        'tablet_id':so['tablet_id'],
                        'delivery_remark':so['delivery_remark'],
                        'location_id':so['location_id'],
                        'deduction_amount':so['deduction_amount'],
                        'user_id':so['user_id'],
                        'name':so['name'],
                        'paid_amount':so['paid_amount'],
                        'partner_id': partner_id,
                        'sale_plan_name':so['sale_plan_day_name'],
                        'additional_discount':so['additional_discount'],
                        'amount_total':so['amount_total'],
                        'type':so['type'],
                        'void_flag':so['void_flag'],
                        'sale_team':so['sale_team'],
                        'date':so['date'],
                        'remaining_amount':so['remaining_amount'],
                        'change_amount':so['change_amount'],
                        'net_amount':so['discounted_total_amount'],
                        'due_date':so['due_date'],
                        'payment_term':so['payment_term'],
                        'mso_longitude':so['mso_longitude'],
                        'mso_latitude':so['mso_latitude'],
                        'outlet_type':so['outlet_type'] ,
                        'pricelist_id':so['pricelist_id'],
                        'branch_id':branch_id,
                    }
                    s_order_id = mobile_sale_order_obj.create(cursor, user, mso_result, context=context)
                    for sol in sale_order_line:
                        if sol['so_name'] == so['name']:
                                cursor.execute('select id From product_product where id  = %s ', (sol['product_id'],))
                                data = cursor.fetchall()
                                if data:
                                    productId = data[0][0]
                                else:
                                    productId = None
                                
                                if sol['price_unit'] == '0':
                                    foc_val = True
                                else:
                                    foc_val = False

                                mso_line_res = {                                                            
                                  'order_id':s_order_id,
                                  'product_id':productId,
                                  'price_unit':sol['price_unit'],
                                  'product_uos_qty':sol['product_uos_qty'],
                                  'foc': foc_val,
                                  'discount':sol['discount'],
                                  'discount_amt':sol['discount_amt'],
                                  'sub_total':sol['sub_total'],
                                  'uom_id':sol['uom_id']
                                }
                                mobile_sale_order_line_obj.create(cursor, user, mso_line_res, context=context) 
                    sale_order_name_list.append(so['name'])
            print 'True'
            return True       
        except Exception, e:
            print 'False'
            return False 
    
# NZO
    def create_exchange_product(self, cursor, user, vals, context=None):
        print 'vals', vals
        try : 
            product_trans_obj = self.pool.get('product.transactions')
            product_trans_line_obj = self.pool.get('product.transactions.line')
            str = "{" + vals + "}"
            str = str.replace(":''", ":'")  # change Order_id
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace(":'}", ":''}")
            str = str.replace("}{", "}|{")
            
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            product_trans = []
            product_trans_line = []
            for r in result:
                print "length", len(r)
                if len(r) >= 13:
                    product_trans_line.append(r)                   
                else:
                    product_trans.append(r)
            
            if product_trans:
                for pt in product_trans:
                    exchange_type = pt['exchange_type']
                    print 'exchange_type', exchange_type
#                     cursor.execute('select id From res_users where partner_id  = %s ',(so['user_id'],))
#                     data = cursor.fetchall()
#                     if data:
#                         saleManId = data[0][0]
#                     else:
#                         saleManId = None
                    mso_result = {
                        'transaction_id':pt['transaction_id'],
                        'customer_id':pt['customer_id'],
                        'customer_code':pt['customer_code'] ,
                        'team_id':pt['team_id'],
                        'date':pt['date'],
                        'exchange_type':pt['exchange_type'],
                        'void_flag':pt['void_flag'],
                        'location_id':pt['location_id'],
                    }
                    s_order_id = product_trans_obj.create(cursor, user, mso_result, context=context)
                    
                    for ptl in product_trans_line:
                        if ptl['transaction_id'] == pt['transaction_id']:
                            
                                if ptl['exp_date'] is None:
                                    exp_date = None
                                else:
                                    exp_date = ptl['exp_date']
                                
                                if exp_date == '' :
                                    exp_date = None
                                else:
                                    exp_date = exp_date
                                
                                cursor.execute('select uom_id from product_product pp,product_template pt where pp.product_tmpl_id=pt.id and pp.id=%s', (ptl['product_id'],))
                                uom_id = cursor.fetchone()[0]
                                mso_line_res = {                                                            
                                  'transaction_id':s_order_id,
                                  'product_id':ptl['product_id'],
                                  'product_qty':ptl['product_qty'],
                                  'uom_id':uom_id,
                                  'so_No':ptl['so_No'],
                                  'trans_type':ptl['trans_type'],
                                  'transaction_name':ptl['transaction_name'],
                                  'note':ptl['note'],
                                  'exp_date':exp_date,
                                  'batchno':ptl['batchno'],
                                }
                                product_trans_line_obj.create(cursor, user, mso_line_res, context=context)
                    if exchange_type != 'Exchange' and pt['void_flag'] == 'none':
                        product_trans_obj.action_convert_ep(cursor, user, [s_order_id], context=context)

                                    
            print 'Truwwwwwwwwwwwwwwwwwwwwwe'
            return True       
        except Exception, e:
            print 'False'
            return False 
    
    def create_visit(self, cursor, user, vals, context=None):
        
        try:
            print 'vals', vals
            customer_visit_obj = self.pool.get('customer.visit')
            str = "{" + vals + "}"    
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:            
                x = ast.literal_eval(data)                
                result.append(x)
            customer_visit = []
            for r in result:                
                customer_visit.append(r)  
            if customer_visit:
                for vs in customer_visit:
                    cursor.execute('select branch_id from crm_case_section where id=%s', (vs['sale_team_id'],))
                    branch_id = cursor.fetchone()[0]
                    visit_result = {
                        'customer_code':vs['customer_code'],
                        'branch_id':branch_id,
                        'customer_id':vs['customer_id'],
                        'sale_plan_day_id':vs['sale_plan_day_id'],
                        'sale_plan_trip_id':vs['sale_plan_trip_id'] ,
                        'sale_plan_name':vs['sale_plan_name'],
                        'sale_team':vs['sale_team'],
                        'sale_team_id':vs['sale_team_id'],
                        'user_id':vs['user_id'],
                        'date':vs['date'],
                        'tablet_id':vs['tablet_id'],
                        'other_reason':vs['other_reason'],
                        'visit_reason':vs['visit_reason'],
                        'latitude':vs['latitude'],
                        'longitude':vs['longitude'],
                        'image':vs['image'],
                        'image1':vs['image1'],
                        'image2':vs['image2'],
                        'image3':vs['image3'],
                        'image4':vs['image4'],
                    }
                    customer_visit_obj.create(cursor, user, visit_result, context=context)
            return True
        except Exception, e:
            print e            
            return False
                
    def geo_location(self, cr, uid, ids, context=None):
        result = {
                 'name'     : 'Go to Report',
                 'res_model': 'ir.actions.act_url',
                 'type'     : 'ir.actions.act_url',
                 'target'   : 'new',
               }
        data = self.browse(cr, uid, ids)[0]
        latitude = data.mso_latitude
        longitude = data.mso_longitude
        print 'latitude', latitude
        print 'longitude', longitude
        print 'https://www.google.com/maps/@' + str(latitude) + ',' + str(longitude) + ',18z'
        result['url'] = 'https://www.google.com/maps/@' + str(latitude) + ',' + str(longitude) + ',18z'
             
        return result
 
    # MMK   
    def action_convert_so(self, cr, uid, ids, context=None):
        msoObj = self.pool.get('mobile.sale.order')
        partner_obj = self.pool.get('res.partner')
        soObj = self.pool.get('sale.order')
        solObj = self.pool.get('sale.order.line')
        invObj = self.pool.get("sale.advance.payment.inv")
        invoiceObj = self.pool.get('account.invoice')
        voucherObj = self.pool.get('account.voucher')
        voucherLineObj = self.pool.get('account.voucher.line')
        stockPickingObj = self.pool.get('stock.picking')
        stockDetailObj = self.pool.get('stock.transfer_details')
        soResult = {}
        solResult = {}
        accountVResult = {}
        foc = False
        price_unit = 0.0
        soId = so_state = iv_state = default_code = pricelist_id = sale_team_id = analytic_id = invoice_id = journal_id = accountId = voucherId = stockViewResult = wizResult = detailObj = None
        solist = []
        invlist = []
        vlist = []
        invFlag = False
        product_name = ''
        if ids:
            # default price list need in sale order form
#             cr.execute("""select id from product_pricelist where type = 'sale' """)
#             data = cr.fetchall()
#             if data:
#                 pricelist_id = data[0][0]
# old query version 
#                 cr.execute("select TI.sale_team_id from  mobile_sale_order msol,tablets_information TI where msol.tablet_id=TI.id and msol.id=%s", (ids[0],))
#                 sale_team_id = cr.fetchone()
            sale_team_obj = self.browse(cr, uid, ids, context)
            sale_team_id = sale_team_obj.sale_team.id
            cr.execute("select cc.analytic_account_id from crm_case_section cc,mobile_sale_order mso where mso.sale_team=cc.id and mso.id=%s", (ids[0],))
            analytic_id = cr.fetchone()
            if analytic_id:
                try:
                    analytic_id = analytic_id[0][0]
                except Exception, e:
                    analytic_id = analytic_id[0]
            else:
                analytic_id = False

            for ms_ids in msoObj.browse(cr, uid, ids[0], context=context):
                if ms_ids:
                    if ms_ids.void_flag == 'voided':  # they work while payment type not 'cash' and 'credit'
                        so_state = 'cancel'
                    elif ms_ids.void_flag == 'none':
                        so_state = 'draft'
                    cr.execute("select company_id from res_users where id=%s", (ms_ids.user_id.id,))
                    company_id = cr.fetchone()[0]
                    date = datetime.strptime(ms_ids.date, '%Y-%m-%d %H:%M:%S')
                    de_date = date.date()       
                    soResult = {
                                          'date_order':ms_ids.date,
                                           'partner_id':ms_ids.partner_id.id,
                                           'amount_untaxed':ms_ids.amount_total ,
                                           'partner_invoice_id':ms_ids.partner_id.id,
                                           'user_id':ms_ids.user_id.id,
                                           'date_confirm':ms_ids.date,
                                           'amount_total':ms_ids.amount_total,
                                           'order_policy':'manual',
                                           'company_id':company_id,
                                           'payment_term':ms_ids.payment_term.id,
                                            'state':so_state,
                                            'pricelist_id':ms_ids.pricelist_id.id,
                                            'picking_policy':'direct',
                                            'warehouse_id':ms_ids.warehouse_id.id,
                                            'project_id':analytic_id,
                                            'partner_shipping_id':ms_ids.partner_id.id,
                                            # 'shipped':'f',
                                            'tb_ref_no':ms_ids.name,
                                            'sale_plan_name':ms_ids.sale_plan_name,
                                            'payment_type':ms_ids.type,
                                            'section_id':sale_team_id,
                                            'due_date':ms_ids.due_date,
                                            'so_latitude':ms_ids.mso_latitude,
                                            'so_longitude':ms_ids.mso_longitude,
                                             'additional_discount':ms_ids.additional_discount*100,
                                            'deduct_amt':ms_ids.deduction_amount,
                                            'delivery_remark':ms_ids.delivery_remark,
                                            'sale_plan_day_id':ms_ids.sale_plan_day_id.id,
                                            'sale_plan_trip_id':ms_ids.sale_plan_trip_id.id,
                                            'customer_code':ms_ids.customer_code,
                                            'branch_id':ms_ids.branch_id.id,
                                        }
                    soId = soObj.create(cr, uid, soResult, context=context)
                    if soId and ms_ids.order_line:
                        for line_id in ms_ids.order_line:
                            if line_id:
                                if line_id.product_id:
                                    if line_id.product_id:
                                        cr.execute("""select default_code from product_product where product_tmpl_id = %s""", (line_id.product_id.id,))
                                        data = cr.fetchall()
                                        if data:
                                            default_code = data[0][0]
                                        if default_code:
                                            product_name = '[' + default_code + ']' + line_id.product_id.name
                                        else:
                                            product_name = line_id.product_id.name
                                        # FOC with price_unit or foc true, false
                                    if line_id.price_unit == 0.0 or line_id.foc:
                                        foc = True
                                        product_name = 'FOC'
                                        price_unit = 0.0
                                    else:
                                        foc = False
                                        price_unit = line_id.price_unit
                                solResult = {
                                             'order_id':soId,
                                              'product_id':line_id.product_id.id,
                                              'name':product_name,
                                              'price_unit':price_unit,
                                              'product_uom':line_id.uom_id.id,
                                              'product_uom_qty':line_id.product_uos_qty,
                                              'discount':line_id.discount,
                                              'discount_amt':line_id.discount_amt,
                                              'company_id':company_id,  # company_id,
                                              'state':'draft',
                                              'net_total':line_id.sub_total,
                                              'sale_foc':foc
                                           }
                                
                                solObj.create(cr, uid, solResult, context=context)
                                if soId:
                                    soObj.button_dummy(cr, uid, [soId], context=context)  # update the SO
                                    
                if ms_ids and  so_state != 'cancel':
                    if ms_ids.type:
                        solist.append(soId)
                        # type > cash and delivery_remark > delivered
                        if ms_ids.type == 'cash' and ms_ids.delivery_remark == 'delivered':  # Payment Type=>Cash and Delivery Remark=>Delivered
                            # SO Confirm 
                            # journal_id = ms_ids.journal_id.id
                            soObj.action_button_confirm(cr, uid, solist, context=context)
                            # Create Invoice
                            invoice_id = self.create_invoices(cr, uid, solist, context=context)
                            # id update partner form (temporay)
#                             partner_data = invoiceObj.browse(cr, uid, invoice_id, context=context)
#                             partner_id=partner_data.partner_id.id
#                             partner_obj.write(cr,uid,partner_id,{'property_account_receivable':629}, context)
#                             partner = partner_obj.browse(cr, uid, partner_id, context=context)
#                             account_id=partner.property_account_receivable.id
#                             invoiceObj.write(cr,uid,invoice_id,{'account_id':account_id}, context)                            
                            cr.execute('update account_invoice set payment_type=%s ,branch_id =%s,delivery_remark =%s,date_invoice=%s where id =%s', ('cash', ms_ids.branch_id.id, ms_ids.delivery_remark,de_date, invoice_id,))                            
                            invoiceObj.button_reset_taxes(cr, uid, [invoice_id], context=context)
                            if invoice_id and ms_ids.paid == True:
                                invlist = []
                                invlist.append(invoice_id)
                                print 'invoice_id', invoice_id
                            
                                
                                # call the api function
                                # invObj contain => account.invoice(1,) like that
                                invObj = invoiceObj.browse(cr, uid, invoice_id, context=context)
                                print 'invoice_id', invObj
                                invObj.action_date_assign()
                                invObj.action_move_create()
                                invObj.action_number()
                                # validate invoice
                                invObj.invoice_validate()
                                
                                # register Payment
                                # calling the register payment pop-up
#                                 invoiceObj.invoice_pay_customer(cr, uid, invlist, context=context)
#                                 if journal_id:
#                                     cr.execute('select default_debit_account_id from account_journal where id=%s', (journal_id,))
#                                     data = cr.fetchall()
#                                     if data:
#                                         accountId = data[0]
#                                 else:
#                                         raise osv.except_osv(_('Warning!'), _("Insert Journal for Cash Sale"))
# #                                 cr.execute('select id from account_account where lower(name)=%s and active= %s', ('cash', True,))  # which account shall I choose. It is needed.
# #                                 data = cr.fetchall()
# #                                 if data:
# #                                     accountId = data[0]
#                                 if journal_id and accountId:  # cash journal and cash account. If there no journal id or no account id, account invoice is not make payment.
#                                     accountVResult = {
#                                                     'partner_id':invObj.partner_id.id,
#                                                     'amount':invObj.amount_total,
#                                                     'journal_id':journal_id,
#                                                     'date':invObj.date_invoice,
#                                                     'period_id':invObj.period_id.id,
#                                                     'account_id':accountId,
#                                                     'pre_line':True,
#                                                     'type':'receipt'
#                                                     }
#                                     # create register payment voucher
#                                     voucherId = voucherObj.create(cr, uid, accountVResult, context=context)
#                                     
#                                 if voucherId:
#                                     vlist = []
#                                     vlist.append(voucherId)
#                                     # get the voucher lines
#                                     vlresult = voucherObj.recompute_voucher_lines(cr, uid, vlist, invObj.partner_id.id, journal_id, invObj.amount_total, 120, 'receipt', invObj.date_invoice, context=None)
#                                     if vlresult:
#                                         result = vlresult['value']['line_cr_ids'][0]
#                                         result['voucher_id'] = voucherId
#                                         # create the voucher lines
#                                         voucherLineObj.create(cr, uid, result, context=context)
#                                     # invoice register payment done
#                                     voucherObj.button_proforma_voucher(cr, uid, vlist , context=context)
#                                     # invoice paid status is true
#                                     invFlag = True
                            # clicking the delivery order view button
                            stockViewResult = soObj.action_view_delivery(cr, uid, solist, context=context)
                            
                            if stockViewResult:
                                # cr.execute('update stock_move set location_id=%s where picking_id=%s',(ms_ids.location_id.id,stockViewResult['res_id'],))
                                # stockViewResult is form result
                                # stocking id =>stockViewResult['res_id']
                                # click force_assign
                                stockPickingObj.force_assign(cr, uid, stockViewResult['res_id'], context=context)
                                # transfer
                                # call the transfer wizard
                                # change list
                                pickList = []
                                pickList.append(stockViewResult['res_id'])
                                wizResult = stockPickingObj.do_enter_transfer_details(cr, uid, pickList, context=context)
                                # pop up wizard form => wizResult
                                detailObj = stockDetailObj.browse(cr, uid, wizResult['res_id'], context=context)
                                if detailObj:
                                    detailObj.do_detailed_transfer()
                                    
                        if ms_ids.type == 'cash' and ms_ids.delivery_remark == 'none':  # Payment Type=>Cash and Delivery Remark=>None
                            # SO Confirm 
                            soObj.action_button_confirm(cr, uid, solist, context=context)
                            # Create Invoice
                            invoice_id = self.create_invoices(cr, uid, solist, context=context)
#                             #id update partner form (temporay)
#                             partner_data = invoiceObj.browse(cr, uid, invoice_id, context=context)
#                             partner_id=partner_data.partner_id.id
#                             partner_obj.write(cr,uid,partner_id,{'property_account_receivable':629}, context)
#                             partner = partner_obj.browse(cr, uid, partner_id, context=context)
#                             account_id=partner.property_account_receivable.id
#                             invoiceObj.write(cr,uid,invoice_id,{'account_id':account_id}, context)                                    
                            cr.execute('update account_invoice set payment_type=%s ,branch_id =%s,delivery_remark =%s ,date_invoice =%s where id =%s', ('cash', ms_ids.branch_id.id, ms_ids.delivery_remark,de_date, invoice_id,))                            
                            invoiceObj.button_reset_taxes(cr, uid, [invoice_id], context=context)
                            if invoice_id and ms_ids.paid == True:
                                invlist = []
                                invlist.append(invoice_id)
                                # call the api function
                                # invObj contain => account.invoice(1,) like that
                                invObj = invoiceObj.browse(cr, uid, invlist, context=context)
                                invObj.action_date_assign()
                                invObj.action_move_create()
                                invObj.action_number()
                                # validate invoice
                                invObj.invoice_validate()
                                
                                # register Payment
                                # calling the register payment pop-up
#                                 invoiceObj.invoice_pay_customer(cr, uid, invlist, context=context)
#                                 cr.execute('select id from account_journal where type=%s', ('cash',))
#                                 data = cr.fetchall()
#                                 if data:
#                                     journal_id = data[0]
#                                 cr.execute('select id from account_account where lower(name)=%s and active= %s', ('cash', True,))  # which account shall I choose. It is needed.
#                                 data = cr.fetchall()
#                                 if data:
#                                     accountId = data[0]
#                                 if journal_id and accountId:  # cash journal and cash account. If there no journal id or no account id, account invoice is not make payment.
#                                     accountVResult = {
#                                                     'partner_id':invObj.partner_id.id,
#                                                     'amount':invObj.amount_total,
#                                                     'journal_id':journal_id,
#                                                     'date':invObj.date_invoice,
#                                                     'period_id':invObj.period_id.id,
#                                                     'account_id':accountId,
#                                                     'pre_line':True,
#                                                     'type':'receipt'
#                                                     }
#                                     # create register payment voucher
#                                     voucherId = voucherObj.create(cr, uid, accountVResult, context=context)
#                                     
#                                 if voucherId:
#                                     vlist = []
#                                     vlist.append(voucherId)
#                                     # get the voucher lines
#                                     vlresult = voucherObj.recompute_voucher_lines(cr, uid, vlist, invObj.partner_id.id, journal_id, invObj.amount_total, 120, 'receipt', invObj.date_invoice, context=None)
#                                     if vlresult:
#                                         result = vlresult['value']['line_cr_ids'][0]
#                                         result['voucher_id'] = voucherId
#                                         # create the voucher lines
#                                         voucherLineObj.create(cr, uid, result, context=context)
#                                     # invoice register payment done
#                                     voucherObj.button_proforma_voucher(cr, uid, vlist , context=context)
#                                     # invoice paid status is true
#                                     invFlag = True
                            # clicking the delivery order view button
                            stockViewResult = soObj.action_view_delivery(cr, uid, solist, context=context)
                            # cr.execute('update stock_move set location_id=%s where picking_id=%s',(ms_ids.location_id.id,stockViewResult['res_id'],))
                            # create the delivery with draft state
                        if ms_ids.type == 'cash' and ms_ids.delivery_remark == 'partial':  # Payment Type=>Cash and Delivery Remark=>None
                            # SO Confirm 
                            soObj.action_button_confirm(cr, uid, solist, context=context)
                            # Create Invoice
                            invoice_id = self.create_invoices(cr, uid, solist, context=context)
                            # id update partner form (temporay)
#                             partner_data = invoiceObj.browse(cr, uid, invoice_id, context=context)
#                             partner_id=partner_data.partner_id.id
#                             partner_obj.write(cr,uid,partner_id,{'property_account_receivable':629}, context)
#                             partner = partner_obj.browse(cr, uid, partner_id, context=context)
#                             account_id=partner.property_account_receivable.id
#                             invoiceObj.write(cr,uid,invoice_id,{'account_id':account_id}, context)                                    
                            cr.execute('update account_invoice set payment_type=%s ,branch_id =%s,delivery_remark =%s,date_invoice=%s  where id =%s', ('cash', ms_ids.branch_id.id, ms_ids.delivery_remark,de_date, invoice_id,))                            
                            invoiceObj.button_reset_taxes(cr, uid, [invoice_id], context=context)
                            if invoice_id and ms_ids.paid == True:
                                invlist = []
                                invlist.append(invoice_id)
                                # call the api function
                                # invObj contain => account.invoice(1,) like that
                                invObj = invoiceObj.browse(cr, uid, invoice_id, context=context)
                                invObj.action_date_assign()
                                invObj.action_move_create()
                                invObj.action_number()
                                # validate invoice
                                invObj.invoice_validate()
                                
                                # register Payment
                                # calling the register payment pop-up
#                                 invoiceObj.invoice_pay_customer(cr, uid, invlist, context=context)
#                                 cr.execute('select id from account_journal where type=%s', ('cash',))
#                                 data = cr.fetchall()
#                                 if data:
#                                     journal_id = data[0]
#                                 cr.execute('select id from account_account where lower(name)=%s and active= %s and type=%s ', ('cash', True, 'liquidity',))  # which account shall I choose. It is needed.
#                                 data = cr.fetchall()
#                                 if data:
#                                     accountId = data[0]
#                                 if journal_id and accountId:  # cash journal and cash account. If there no journal id or no account id, account invoice is not make payment.
#                                     accountVResult = {
#                                                     'partner_id':invObj.partner_id.id,
#                                                     'amount':invObj.amount_total,
#                                                     'journal_id':journal_id,
#                                                     'date':invObj.date_invoice,
#                                                     'period_id':invObj.period_id.id,
#                                                     'account_id':accountId,
#                                                     'pre_line':True,
#                                                     'type':'receipt'
#                                                     }
#                                     # create register payment voucher
#                                     voucherId = voucherObj.create(cr, uid, accountVResult, context=context)
#                                     
#                                 if voucherId:
#                                     vlist = []
#                                     vlist.append(voucherId)
#                                     # get the voucher lines
#                                     vlresult = voucherObj.recompute_voucher_lines(cr, uid, vlist, invObj.partner_id.id, journal_id, invObj.amount_total, 120, 'receipt', invObj.date_invoice, context=None)
#                                     if vlresult:
#                                         result = vlresult['value']['line_cr_ids'][0]
#                                         result['voucher_id'] = voucherId
#                                         # create the voucher lines
#                                         voucherLineObj.create(cr, uid, result, context=context)
#                                     # invoice register payment done
#                                     voucherObj.button_proforma_voucher(cr, uid, vlist , context=context)
#                                     # invoice paid status is true
#                                     invFlag = True
                            # clicking the delivery order view button
                            stockViewResult = soObj.action_view_delivery(cr, uid, solist, context=context)
                            # cr.execute('update stock_move set location_id=%s where picking_id=%s',(ms_ids.location_id.id,stockViewResult['res_id'],))
                            # create the delivery with draft state
                        if ms_ids.type == 'credit' and ms_ids.delivery_remark == 'delivered':  # Payment Type=>Credit and Delivery Remark=>Delivered
                            # so Confirm
                            print 'solist', solist
                            soObj.action_button_confirm(cr, uid, solist, context=context)
                            # invoice create at draft state
                            invoice_id = self.create_invoices(cr, uid, solist, context=context)
                            # id update partner form (temporay)
#                             partner_data = invoiceObj.browse(cr, uid, invoice_id, context=context)
#                             partner_id=partner_data.partner_id.id
#                             partner_obj.write(cr,uid,partner_id,{'property_account_receivable':629}, context)
#                             partner = partner_obj.browse(cr, uid, partner_id, context=context)
#                             account_id=partner.property_account_receivable.id
#                             invoiceObj.write(cr,uid,invoice_id,{'account_id':account_id}, context)                                    
                            cr.execute('update account_invoice set payment_type=%s ,branch_id =%s,delivery_remark =%s ,date_invoice=%s where id =%s', ('credit', ms_ids.branch_id.id, ms_ids.delivery_remark,de_date, invoice_id,))                            
                            invoiceObj.button_reset_taxes(cr, uid, [invoice_id], context=context)
                            invlist = []
                            invlist.append(invoice_id)
                            # call the api function
                            # invObj contain => account.invoice(1,) like that
                            invObj = invoiceObj.browse(cr, uid, invoice_id, context=context)
                            invObj.action_date_assign()
                            invObj.action_move_create()
                            invObj.action_number()
                            # validate invoice
                            invObj.invoice_validate()
                            # clicking the delivery order view button
                            stockViewResult = soObj.action_view_delivery(cr, uid, solist, context=context)
                            if stockViewResult:
                                # cr.execute('update stock_move set location_id=%s where picking_id=%s',(ms_ids.location_id.id,stockViewResult['res_id'],))

                                # stockViewResult is form result
                                # stocking id =>stockViewResult['res_id']
                                # click force_assign
                                stockPickingObj.force_assign(cr, uid, stockViewResult['res_id'], context=context)
                                # transfer
                                # call the transfer wizard
                                # change list
                                pickList = []
                                pickList.append(stockViewResult['res_id'])
                                wizResult = stockPickingObj.do_enter_transfer_details(cr, uid, pickList, context=context)
                                # pop up wizard form => wizResult
                                detailObj = stockDetailObj.browse(cr, uid, wizResult['res_id'], context=context)
                                if detailObj:
                                    detailObj.do_detailed_transfer()

                        if ms_ids.type == 'credit' and ms_ids.delivery_remark == 'none':  # Payment Type=>Credit and Delivery Remark=>None
                            # so Confirm
                            soObj.action_button_confirm(cr, uid, solist, context=context)
                            # invoice create at draft state
                            invoice_id = self.create_invoices(cr, uid, solist, context=context)
                            # id update partner form (temporay)
#                             partner_data = invoiceObj.browse(cr, uid, invoice_id, context=context)
#                             partner_id=partner_data.partner_id.id
#                             partner_obj.write(cr,uid,partner_id,{'property_account_receivable':629}, context)
#                             partner = partner_obj.browse(cr, uid, partner_id, context=context)
#                             account_id=partner.property_account_receivable.id
#                             invoiceObj.write(cr,uid,invoice_id,{'account_id':account_id}, context)                                    
                            cr.execute('update account_invoice set payment_type=%s ,branch_id =%s,delivery_remark =%s,date_invoice=%s  where id =%s', ('credit', ms_ids.branch_id.id, ms_ids.delivery_remark,de_date, invoice_id,))                            
                            invoiceObj.button_reset_taxes(cr, uid, [invoice_id], context=context)
                            invlist = []
                            invlist.append(invoice_id)
                            # call the api function
                            # invObj contain => account.invoice(1,) like that
                            invObj = invoiceObj.browse(cr, uid, invoice_id, context=context)
                            invObj.action_date_assign()
                            invObj.action_move_create()
                            invObj.action_number()
                            # validate invoice
                            invObj.invoice_validate()
                            # clicking the delivery order view button
                            stockViewResult = soObj.action_view_delivery(cr, uid, solist, context=context)  # create delivery order with draft state
                            # cr.execute('update stock_move set location_id=%s where picking_id=%s',(ms_ids.location_id.id,stockViewResult['res_id'],))

                        if ms_ids.type == 'credit' and ms_ids.delivery_remark == 'partial':  # Payment Type=>Credit and Delivery Remark=>Partial
                            # so Confirm
                            soObj.action_button_confirm(cr, uid, solist, context=context)
                            # invoice create at draft state
                            invoice_id = self.create_invoices(cr, uid, solist, context=context)
                            # id update partner form (temporay)
#                             partner_data = invoiceObj.browse(cr, uid, invoice_id, context=context)
#                             partner_id=partner_data.partner_id.id
#                             partner_obj.write(cr,uid,partner_id,{'property_account_receivable':629}, context)
#                             partner = partner_obj.browse(cr, uid, partner_id, context=context)
#                             account_id=partner.property_account_receivable.id
#                             invoiceObj.write(cr,uid,invoice_id,{'account_id':account_id}, context)                                    
                            cr.execute('update account_invoice set payment_type=%s ,branch_id =%s,delivery_remark =%s ,date_invoice=%s where id =%s', ('credit', ms_ids.branch_id.id, ms_ids.delivery_remark,de_date,invoice_id,))                            
                            
                            invoiceObj.button_reset_taxes(cr, uid, [invoice_id], context=context)
                            invlist = []
                            invlist.append(invoice_id)
                            # call the api function
                            # invObj contain => account.invoice(1,) like that
                            invObj = invoiceObj.browse(cr, uid, invoice_id, context=context)
                            invObj.action_date_assign()
                            invObj.action_move_create()
                            invObj.action_number()
                            # validate invoice
                            invObj.invoice_validate()
                            # clicking the delivery order view button
                            stockViewResult = soObj.action_view_delivery(cr, uid, solist, context=context)
                            # cr.execute('update stock_move set location_id=%s where picking_id=%s',(ms_ids.location_id.id,stockViewResult['res_id'],))

            self.write(cr, uid, ids[0], {'m_status':'done'}, context=context)
        return True   
    
    # MMK
    def create_invoices(self, cr, uid, ids, context=None):
        """ create invoices for the active sales orders """
        print 'Sale Order ID', ids  
        sale_obj = self.pool.get('sale.order')
        sale_ids = ids
        if sale_ids:
            # create the final invoices of the active sales orders
            print 'YOOOOOOOOOOOOO', sale_ids
            try:
                print 'Create Invoice Context', context
                res = sale_obj.manual_invoice(cr, uid, sale_ids, context=context)          
                return res['res_id']
            except Exception, e:
                return False
                
    # kzo Edit
    def get_products_by_sale_team(self, cr, uid, section_id , last_date, context=None, **kwargs):
        
        cr.execute('''select  pp.id,pt.list_price , coalesce(replace(pt.description,',',';'), ' ') as description,pt.categ_id,pc.name as categ_name,pp.default_code, 
                         pt.name,substring(replace(cast(pt.image_small as text),'/',''),1,5) as image_small,pt.main_group,pt.uom_ratio,
                         pp.product_tmpl_id,pt.is_foc,pp.sequence
                        from crm_case_section_product_product_rel crm_real ,
                        crm_case_section ccs ,product_template pt, product_product pp , product_category pc
                        where pp.id = crm_real.product_product_id
                        and pt.id = pp.product_tmpl_id
                        and pt.active = true
                        and pp.active = true
                        and ccs.id = crm_real.crm_case_section_id
                        and pc.id = pt.categ_id                        
                        and ccs.id = %s ''', (section_id,))
        datas = cr.fetchall()
        return datas
    
    def get_salePlanDays_by_sale_team(self, cr, uid, section_id , context=None, **kwargs):
        cr.execute('''select id,name,date,sale_team from sale_plan_day where sale_team=%s ''', (section_id,))
        datas = cr.fetchall()
        cr.execute
        return datas
    
    # get promotion datas from database
    def get_products_categ_by_sale_team(self, cr, uid, section_id , context=None, **kwargs):
        cr.execute('''select distinct categ_id,categ_name from (
                        select pp.product_tmpl_id,pt.list_price , pt.description,pt.categ_id,pc.name as categ_name from crm_case_section_product_product_rel crm_real ,
                        crm_case_section ccs ,product_template pt, product_product pp , product_category pc
                        where pp.id = crm_real.product_product_id
                        and pt.id = pp.product_tmpl_id
                        and ccs.id = crm_real.crm_case_section_id
                        and pc.id = pt.categ_id
                        and ccs.id = %s
                        )A ''', (section_id,))
        datas = cr.fetchall()
        cr.execute
        return datas
    # get promotion datas from database
    
    def get_promos_datas(self, cr, uid , branch_id, state, team_id, context=None, **kwargs):
   
        if state == 'approve':
            status = 'approve'
            cr.execute('''select id,sequence as seq,from_date ,to_date,active,name as p_name,
                        logic ,expected_logic_result ,special, special1, special2, special3 ,description,
                        pr.promotion_count, pr.monthly_promotion
                        from promos_rules pr ,promos_rules_res_branch_rel pro_br_rel
                        where pr.active = true                     
                        and pr.id = pro_br_rel.promos_rules_id
                        and pro_br_rel.res_branch_id = %s
                        and pr.state = %s
                        and  now()::date  between from_date::date and to_date::date
                        and pr.id in (
                        select a.promo_id from promo_sale_channel_rel a
                        inner join sale_team_channel_rel b
                        on a.sale_channel_id = b.sale_channel_id
                        where b.sale_team_id = %s
                        )
                        ''', (branch_id, status, team_id,))
        else:
            status = 'approve', 'draft'            
            cr.execute('''select id,sequence as seq,from_date ,to_date,active,name as p_name,
                        logic ,expected_logic_result ,special, special1, special2, special3 ,description,
                        pr.promotion_count, pr.monthly_promotion
                        from promos_rules pr ,promos_rules_res_branch_rel pro_br_rel
                        where pr.active = true                     
                        and pr.id = pro_br_rel.promos_rules_id
                        and pro_br_rel.res_branch_id = %s
                        and pr.state in %s
                        and  now()::date  between from_date::date and to_date::date
                        and pr.id in (
                        select a.promo_id from promo_sale_channel_rel a
                        inner join sale_team_channel_rel b
                        on a.sale_channel_id = b.sale_channel_id
                        where b.sale_team_id = %s
                        )
                        ''', (branch_id, status, team_id,))
        datas = cr.fetchall()        
        return datas
    
    def get_promos_act_datas(self, cr, uid , branch_id, promo_id, context=None, **kwargs):
        cr.execute('''select act.id,act.promotion,act.sequence as act_seq ,act.arguments,act.action_type,act.product_code
                            from promos_rules r ,promos_rules_actions act,promos_rules_res_branch_rel pro_br_rel
                            where r.id = act.promotion
                            and r.active = 't'                            
                            and r.id = pro_br_rel.promos_rules_id
                            and pro_br_rel.res_branch_id = %s
                            and act.promotion = %s                    
                    ''', (branch_id, promo_id,))
        datas = cr.fetchall()
        cr.execute
        return datas
    def get_promos_cond_datas(self, cr, uid , branch_id, promo_id, context=None, **kwargs):
        cr.execute('''select cond.id,cond.promotion,cond.sequence as cond_seq,
                            cond.attribute as cond_attr,cond.comparator as cond_comparator,
                            cond.value as comp_value
                            from promos_rules r ,promos_rules_conditions_exps cond,promos_rules_res_branch_rel pro_br_rel
                            where r.id = cond.promotion
                            and r.active = 't'                           
                            and r.id = pro_br_rel.promos_rules_id
                            and pro_br_rel.res_branch_id = %s
                            and cond.promotion = %s  
                    ''', (branch_id, promo_id,))
        datas = cr.fetchall()
        cr.execute
        return datas
   
    def get_promos_rule_partner_datas(self, cr, uid , context=None, **kwargs):
        cr.execute('''select category_id,rule_id from rule_partner_cat_rel''')
        datas = cr.fetchall()
        cr.execute
        return datas
    def get_promos_category_datas(self, cr, uid , context=None, **kwargs):
        cr.execute('''select id,name from res_partner_category''')
        datas = cr.fetchall()
        cr.execute
        return datas
    # get Mobile Sale Order Datas
    def get_mobile_so_datas(self, cr, uid, todayDateNormal, saleTeamId, saleorderList, context=None, **kwargs):
        saleOrderName = ', '.join(saleorderList) 
        print "sale", str(tuple(saleorderList))
        saleorder = str(tuple(saleorderList))
        mobile_sale_order_obj = self.pool.get('mobile.sale.order')
        list_val = None
        list_val = mobile_sale_order_obj.search(cr, uid, [('due_date', '>', todayDateNormal), ('sale_team', '=', saleTeamId), ('name', 'not in', saleorderList), ('type', '=', 'credit')])
        print 'list_val', list_val
        list = []
        if list_val:
            for val in list_val:
                cr.execute('select id,void_flag,name,create_date,date,partner_id,customer_code,sale_plan_trip_id,sale_plan_day_id,user_id,amount_total,type,delivery_remark,additional_discount,deduction_amount,paid_amount,paid,tablet_id,warehouse_id,location_id,sale_team,due_date,payment_term,mso_latitude,mso_longitude,remaining_amount,change_amount,net_amount from mobile_sale_order where id=%s', (val,))
                result = cr.fetchall()
                list.append(result)
                print' list', list
        return list
    # get Mobile Sale Order Line Datas
    def get_mobile_soline_datas(self, cr, uid, todayDateNormal, so_ids, context=None, **kwargs):
        print 'So_ids', so_ids
        order_ids = so_ids
#         order_ids = map(int, so_ids)
#         print 'Map Order Id',order_ids
        mobile_so_line_obj = self.pool.get('mobile.sale.order.line')
        list_val = None
        list_val = mobile_so_line_obj.search(cr, uid, [('create_date', '>', todayDateNormal), ('order_id', 'in', order_ids)])
        print 'list_val', list_val
        list = []
        if list_val:
            for val in list_val:
                cr.execute('select id,product_id,product_uos_qty,price_unit,discount,sub_total,order_id from mobile_sale_order_line where id=%s', (val,))
                result = cr.fetchall()
                list.append(result)
                print' list', list
        return list    

    def get_pricelist_datas(self, cr, uid , section_id, context=None, **kwargs):
        cr.execute('''select ppl.id,ppl.name,ppl.type, ppl.active , cpr.is_default
                 from price_list_line cpr , product_pricelist ppl
                 where ppl.id = cpr.property_product_pricelist 
                 and ppl.active = true
                 and cpr.team_id = %s''', (section_id,))
        datas = cr.fetchall()
        print 'Price List Data', datas
        return datas
    
    def get_pricelist_version_datas(self, cr, uid, pricelist_id, context=None, **kwargs):
        cr.execute('''select pv.id,date_end,date_start,pv.active,pv.name,pv.pricelist_id 
                        from product_pricelist_version pv, product_pricelist pp where pv.pricelist_id = pp.id   
                        and pv.active = true                                                         
                        and pv.pricelist_id = %s''', (pricelist_id,))
        datas = cr.fetchall()
        return datas
    
    def get_pricelist_item_datas(self, cr, uid, version_id, context=None, **kwargs):
        cr.execute('''select pi.id,pi.price_discount,pi.sequence,pi.product_tmpl_id,pi.name,pp.id base_pricelist_id,
                    pi.product_id,pi.base,pi.price_version_id,pi.min_quantity,
                    pi.categ_id,pi.new_price price_surcharge,pi.product_uom_id
                    from product_pricelist_item pi, product_pricelist_version pv, product_pricelist pp
                    where pv.pricelist_id = pp.id                             
                    and pv.id = pi.price_version_id
                    and pi.price_version_id = %s''', (version_id,))
        datas = cr.fetchall()        
        return datas

    def get_product_uoms(self, cr, uid , saleteam_id, context=None, **kwargs):
        cr.execute('''
                select distinct uom_id,uom_name,ratio,template_id,product_id from(
                select  pu.id as uom_id,pu.name as uom_name ,1/pu.factor as ratio,
                pur.product_template_id as template_id,pp.id as product_id
                from product_uom pu , product_template_product_uom_rel pur ,
                product_product pp,
                crm_case_section_product_product_rel crm
                where pp.product_tmpl_id = pur.product_template_id
                and crm.product_product_id = pp.id
                and pu.id = pur.product_uom_id
                and crm.crm_case_section_id = %s            
                )A''' , (saleteam_id,))
        datas = cr.fetchall()
        cr.execute
        return datas

    # Get Res Partner and Res Partner Category res_partner_res_partner_category_rel
    def get_res_partner_category_datas(self, cr, uid , context=None, **kwargs):
        cr.execute('''
        select a.category_id, a.partner_id ,b.name
        from res_partner_res_partner_category_rel a , res_partner_category b
        where a.category_id = b.id
        ''')
        datas = cr.fetchall()
        return datas
    
    def get_sale_team_members_datas(self, cr, uid , member_id, saleteam_id, context=None, **kwargs):
        cr.execute('''select u.id as id,u.active as active,u.login as login,u.password as password,u.partner_id as partner_id,p.name as name from res_users u, res_partner p
                   where u.partner_id = p.id and u.id in(select member_id from crm_case_section cr, sale_member_rel sm where sm.section_id = cr.id and cr.id =%s)''', (saleteam_id,)) 
        datas = cr.fetchall()
        cr.execute
        return datas
    def sale_team_return(self, cr, uid, section_id , saleTeamId, context=None, **kwargs):
        cr.execute('''select DISTINCT cr.id,cr.complete_name,cr.warehouse_id,cr.name,sm.member_id,cr.code,pr.product_product_id,cr.location_id
                    from crm_case_section cr, sale_member_rel sm,crm_case_section_product_product_rel pr where sm.section_id = cr.id and cr.id=pr.crm_case_section_id  
                    and sm.member_id =%s 
                    and cr.id = %s
            ''', (section_id, saleTeamId,))
        datas = cr.fetchall()
        cr.execute
        return datas

    def sale_plan_day_return(self, cr, uid, section_id, pull_date , context=None, **kwargs):
        
        lastdate = datetime.strptime(pull_date, "%Y-%m-%d")
        print 'DateTime', lastdate
        
        cr.execute('''            
            select p.id,p.date,p.sale_team,p.name,p.principal,p.week from sale_plan_day p
            join  crm_case_section c on p.sale_team=c.id
            where p.sale_team=%s and p.active = true        
            ''', (section_id,))
        datas = cr.fetchall()
        cr.execute      
        return datas    
    def sale_plan_trip_return(self, cr, uid, section_id, pull_date , context=None, **kwargs):
     
        lastdate = datetime.strptime(pull_date, "%Y-%m-%d")
        print 'DateTime', lastdate
        cr.execute('''            
            select distinct p.id,p.date,p.sale_team,p.name,p.principal from sale_plan_trip p
            ,  crm_case_section c,res_partner_sale_plan_trip_rel d, res_partner e
            where  p.sale_team=c.id
            and p.sale_team= %s
            and p.active = true 
            and p.id = d.sale_plan_trip_id
            and e.id = d.partner_id            
            ''', (section_id,))
        datas = cr.fetchall()                      
        return datas
        
        # kzo
    def stock_picking_type(self, cr, uid , context=None, **kwargs):
        cr.execute('''select id,code from stock_picking_type''')            
        datas = cr.fetchall()        
        return datas
    
    def stock_move_return(self, cr, uid, section_id , context=None, **kwargs):
        cr.execute('''select id,product_qty,product_id,picking_id,state,origin,picking_type_id,location_dest_id,partner_id from stock_move where location_dest_id in(select cr.location_id from crm_case_section cr, sale_member_rel sm where sm.section_id = cr.id and sm.member_id=%s)
            ''', (section_id,))
        datas = cr.fetchall()        
        return datas
    
    def tablet_info(self, cr, uid, tabetId, context=None, **kwargs):    
        cr.execute('''
            select id as tablet_id,date,create_uid,name,note,mac_address,model,type,storage_day
            ,replace(hotline,',',';') hotline,sale_team_id,is_testing
            from tablets_information 
            where name = %s
            ''', (tabetId,))
        datas = cr.fetchall()
        return datas
    
    def get_company_datas(self, cr, uid , context=None):        
        cr.execute('''select id,name from res_company''')
        datas = cr.fetchall()        
        return datas
    
    def get_res_users(self, cr, uid, user_id , context=None, **kwargs):
        cr.execute('''
            select id,active,login,password,partner_id,branch_id ,
            (select uid from res_groups_users_rel where gid in (select id from res_groups  
            where name='Allow To Active') and uid= %s) allow_to_active
            from res_users 
            where id = %s
            ''', (user_id,user_id,))
        datas = cr.fetchall()        
        return datas
    
    def check_account(self, cr, uid, login, pwd, sale_team_id, context=None, **kwargs):
        cr.execute('''
            select c.name as TabletName,D.userid,D.login,D.login_password from(
            select name,sale_team_id from tablets_information
            )C inner join(
            select A.userid,A.login,A.login_password,B.id as saleTeamId from(
            select id as userid,login,login_password from res_users
            )A inner join(
            select DISTINCT cr.id as id,cr.complete_name,cr.warehouse_id,cr.name,sm.member_id,cr.code,cr.location_id
                    from crm_case_section cr, sale_member_rel sm
                    where sm.section_id = cr.id
            ) B on A.userid = B.member_id
            )D on c.sale_team_id = D.saleTeamId
            where c.name = %s
            and D.login= %s
            and d.login_password = crypt(%s, login_password)
            ''', (sale_team_id, login, pwd,))
        datas = cr.fetchall()
        if datas:
            flag = True
        else:
            flag = False            
        return flag  
       
 # Create Sync for promotion line by kzo
    def create_promotion_line(self, cursor, user, vals, context=None):
        
        try : 
            mso_promotion_line_obj = self.pool.get('mso.promotion.line')
            str = "{" + vals + "}"
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            promo_line = []
            for r in result:                
                promo_line.append(r)  
            if promo_line:
                for pro_line in promo_line:
                
                    cursor.execute('select id From mobile_sale_order where name  = %s ', (pro_line['promo_line_id'],))
                    data = cursor.fetchall()
                    if data:
                        saleOrder_Id = data[0][0]
                    else:
                        saleOrder_Id = None
                    
                    promo_line_result = {
                        'promo_line_id':saleOrder_Id,
                        'pro_id':pro_line['pro_id'],
                        'from_date':pro_line['from_date'],
                        'to_date':pro_line['to_date'] ,
                        }
                    mso_promotion_line_obj.create(cursor, user, promo_line_result, context=context)
            return True
        except Exception, e:
            return False
    
    def create_dsr_notes(self, cursor, user, vals, context=None):
        print 'vals', vals
        try : 
            history_obj = self.pool.get('sales.denomination')
            notes_line_obj = self.pool.get('sales.denomination.note.line')
            deno_product_obj = self.pool.get('sales.denomination.product.line')
            cheque_product_obj = self.pool.get('sales.denomination.cheque.line')
            ar_coll_obj = self.pool.get('sales.denomination.ar.line')
            bank_transfer_obj = self.pool.get('sales.denomination.bank.line')
            ar_obj = self.pool.get('ar.payment')
            inv_Obj=self.pool.get('account.invoice')
            invoice_obj = self.pool.get('account.invoice.line')
            ar_amount=0.0
            product_amount=0.0
            deno_amount=0.0
            cheque_amount = 0.0
            bank_amount=0.0
            dssr_ar_amount=0.0
            trans_amount=0.0
            diff_amount=0.0
            discount_amount=0.0
            discount_total=0.0
            invoice_sub_total=0.0
            m_discount_total=0.0
            m_discount_amount=0.0
            v_discount_total=0.0
            v_discount_amount=0.0
            str = "{" + vals + "}"
            str = str.replace(":''", ":'")
            str = str.replace("'',", "',")
            str = str.replace(":',", ":'',")
            str = str.replace(":'}", ":''}")
            str = str.replace("}{", "}|{")
            
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
           
            history = []
            notes_line = []
            
            for r in result:                
                if len(r) >= 7:
                    history.append(r)                   
                else:
                    notes_line.append(r)
            
            if history:
                print 'hidtory', history
                for pt in history:
                    print 'dateImmmm',datetime.today().strftime('%d-%m-%Y %H:%M:%S'  )
                    deno_result = {
                        'invoice_count':pt['invoice_count'],
                        'sale_team_id':pt['sale_team_id'],
                        'company_id':pt['company_id'] ,
                        'note':pt['note'],
                        'date': datetime.today().strftime('%Y-%m-%d %H:%M:%S' ),
                        'tablet_id':pt['tablet_id'],
                        'user_id':pt['user_id'],
                        'denomination_note_line':False,
                        'denomination_product_line':False,
                        'denomination_ar_line':False,
                        'denomination_cheque_line':False,
                        'denomination_bank_line':False,
                        'branch_id':pt['branch_id'],
                        'total_amount':0,
                        'diff_amount':0,
                        'product_amount':0,
                        'discount_amount':0,
                        'discount_total':0,
                        'invoice_sub_total':0,
                    }
                    deno_id = history_obj.create(cursor, user, deno_result, context=context)             
                    for ptl in notes_line:
                                deno_amount+= float(ptl['amount'])
                                note_line_res = {                                                            
                                  'denomination_note_ids':deno_id,
                                  'note_qty':ptl['note_qty'],
                                  'notes':ptl['notes'],
                                  'amount':ptl['amount'],
                                }
                                notes_line_obj.create(cursor, user, note_line_res, context=context)
                de_date = pt['date']
                user_id = pt['user_id']      
                pre_mobile_ids=[]
                mobile_ids=[]
                mobile_sale_obj = self.pool.get('mobile.sale.order')        
                mobile_sale_order_obj = self.pool.get('mobile.sale.order.line')
                pre_sale_order_obj = self.pool.get('pre.sale.order.line')
                payment_obj = self.pool.get('customer.payment')
                print 'user_iddddddddddddd', user_id, type(user_id)
                cursor.execute("select default_section_id from res_users where id=%s", (user_id,))
                team_id = cursor.fetchone()[0]            
                print 'team_id', team_id,de_date
                cursor.execute("select id from customer_payment where date=%s and sale_team_id=%s and cheque_no !=''  ", (de_date, team_id,))
                payment_ids = cursor.fetchall()
                cursor.execute("select id from ar_payment where date=%s and sale_team_id=%s and payment_code='CHEQ' ", (de_date, team_id,))
                ar_payment_ids = cursor.fetchall()
                cursor.execute("select id from customer_payment where date=%s and sale_team_id=%s and payment_code='BNK' ", (de_date, team_id,))
                bank_ids = cursor.fetchall()
                cursor.execute("select id from ar_payment where date=%s and sale_team_id=%s and payment_code='BNK' ", (de_date, team_id,))
                ar_bank_ids = cursor.fetchall()                              
                cursor.execute("select id from mobile_sale_order where due_date=%s and user_id=%s and void_flag != 'voided'", (de_date, user_id))
                m_mobile_ids = cursor.fetchall()
                cursor.execute("select id from account_invoice where date_invoice=%s and section_id =%s and state='open' ", (de_date, team_id,))
                invoice_ids = cursor.fetchall()       
                if invoice_ids:
                    for data_pro in invoice_ids:
                        pre_mobile_ids.append(data_pro[0])
                if pre_mobile_ids:
                    invoice_data = inv_Obj.search(cursor, user, [('id', 'in', tuple(pre_mobile_ids))], context=context)   
                    for invoice_id in invoice_data:
                        invoice =inv_Obj.browse(cursor, user, invoice_id, context=context)
                        deduct_amt= invoice.deduct_amt
                        amount_total= invoice.amount_untaxed
                        deduct_percent=invoice.additional_discount/100
                        discount_total +=  amount_total * deduct_percent
                        discount_amount+=deduct_amt                    
                    line_ids = invoice_obj.search(cursor, user, [('invoice_id', 'in', pre_mobile_ids)], context=context)         
                    order_line_ids = invoice_obj.browse(cursor, user, line_ids, context=context)         
                    cursor.execute(' select product_id,sum(quantity) as quantity,sum(price_subtotal) as  sub_total from account_invoice_line where id in %s group by product_id', (tuple(order_line_ids.ids),))
                    order_line = cursor.fetchall()
                    for data in order_line:
                        product = self.pool.get('product.product').browse(cursor, user, data[0], context=context)
                        sequence = product.sequence
                        product_amount+=data[2]
                        data_id = {'product_id':data[0],
                                          'product_uom_qty':data[1],
                                          'denomination_product_ids':deno_id,
                                          'sequence':sequence,
                                          'amount':data[2]}
                        deno_product_obj.create(cursor, user, data_id, context=context)                        
                if  m_mobile_ids:
                    for data_mo in m_mobile_ids:
                        mobile_ids.append(data_mo[0])
                    mobile_data=mobile_sale_obj.browse(cursor, user, tuple(mobile_ids), context=context)           
                    print 'mobile_data',mobile_data
                    for mobile in mobile_data:
                        deduct_amt= mobile.deduction_amount
                        amount_total= mobile.amount_total
                        deduct_percent=mobile.additional_discount
                        discount_total +=  amount_total * deduct_percent
                        discount_amount+=deduct_amt                             
                    line_ids = mobile_sale_order_obj.search(cursor, user, [('order_id', 'in', mobile_ids)], context=context)                        
                    order_line_ids = mobile_sale_order_obj.browse(cursor, user, line_ids, context=context)                
                    cursor.execute('select product_id,sum(product_uos_qty),sum(sub_total) from mobile_sale_order_line where id in %s group by product_id', (tuple(order_line_ids.ids),))
                    order_line = cursor.fetchall()
                    for data in order_line:
                        product = self.pool.get('product.product').browse(cursor, user, data[0], context=context)
                        sequence = product.sequence
                        product_amount+=data[2]
                        data_id = {'product_id':data[0],
                                          'product_uom_qty':data[1],
                                          'denomination_product_ids':deno_id,
                                          'sequence':sequence,
                                          'amount':data[2]}
                        deno_product_obj.create(cursor, user, data_id, context=context)
            if  payment_ids:
                for payment in payment_ids:
                    payment_data = payment_obj.browse(cursor, user, payment, context=context)                  
                    partner_id = payment_data.partner_id.id
                    journal_id = payment_data.journal_id.id
                    cheque_no = payment_data.cheque_no
                    amount = payment_data.amount
                    cheque_amount += payment_data.amount
                    data_id = {'partner_id':partner_id,
                                      'journal_id':journal_id,
                                      'cheque_no':cheque_no,
                                      'amount': amount,
                                    'denomination_cheque_ids':deno_id, }
                    cheque_product_obj.create(cursor, user, data_id, context=context)
            if  ar_payment_ids:
                for payment in ar_payment_ids:
                    payment_data = ar_obj.browse(cursor, user, payment, context=context)                  
                    partner_id = payment_data.partner_id.id
                    journal_id = payment_data.journal_id.id
                    cheque_no = payment_data.cheque_no
                    amount = payment_data.amount
                    cheque_amount += payment_data.amount
                    data_id = {'partner_id':partner_id,
                                      'journal_id':journal_id,
                                      'cheque_no':cheque_no,
                                      'amount': amount,
                                     'denomination_cheque_ids':deno_id,
                                      }
                    cheque_product_obj.create(cursor, user, data_id, context=context)
            if  bank_ids:
                for bank in bank_ids:
                    bank_data = payment_obj.browse(cursor, user, bank, context=context)                  
                    partner_id = bank_data.partner_id.id
                    journal_id = bank_data.journal_id.id
                    amount = bank_data.amount
                    bank_amount += bank_data.amount
                    data_id = {'partner_id':partner_id,
                                      'journal_id':journal_id,
                                      'amount': amount,
                                        'denomination_bank_ids':deno_id, }
                    bank_transfer_obj.create(cursor, user, data_id, context=context)
            if  ar_bank_ids:
                for bank in ar_bank_ids:
                    bank_data = ar_obj.browse(cursor, user, bank, context=context)                  
                    partner_id = bank_data.partner_id.id
                    journal_id = bank_data.journal_id.id
                    amount = bank_data.amount
                    bank_amount += bank_data.amount
                    data_id = {'partner_id':partner_id,
                                      'journal_id':journal_id,
                                      'amount': amount,
                                        'denomination_bank_ids':deno_id, }
                    bank_transfer_obj.create(cursor, user, data_id, context=context)
            cursor.execute("""select m.date,a.id,m.partner_id,m.payment_amount
                                from account_invoice as a,mobile_ar_collection as m
                                where m.ref_no = a.number and  m.state='draft'  and
                                m.user_id=%s and m.sale_team_id=%s and m.date = %s  
                    """, (user_id, team_id, de_date,))
            vals = cursor.fetchall()             
            print 'vals', vals
            for val in vals:
                ar_amount +=val[3]
                data_id = {'invoice_id':val[1],
                            'date':val[0],
                            'partner_id':val[2],
                            'amount':val[3],
                            'payment_type':'Credit',
                         'denomination_ar_ids':deno_id, }
                ar_coll_obj.create(cursor, user, data_id, context=context)
            dssr_ar_amount=ar_amount+product_amount- discount_amount-discount_total
            trans_amount= deno_amount + cheque_amount + bank_amount
            diff_amount= (ar_amount+product_amount- discount_amount-discount_total)-( deno_amount + cheque_amount + bank_amount)             
            invoice_sub_total=product_amount - discount_amount-discount_total
            product_amount=product_amount-discount_amount-discount_total
            print 'discount_total',discount_total,discount_amount
            cursor.execute("update sales_denomination set product_amount=%s,discount_total=%s,discount_amount =%s,invoice_sub_total=%s,ar_amount=%s,bank_amount=%s,total_amount=%s,cheque_amount=%s ,dssr_ar_amount=%s,trans_amount=%s ,diff_amount=%s where id=%s",
                           (product_amount,discount_total,discount_amount,invoice_sub_total,ar_amount,bank_amount,deno_amount,cheque_amount,dssr_ar_amount,trans_amount,diff_amount,deno_id,))
                        
            print 'True'
            return True       
        except Exception, e:
            return False
        
    def create_ar_collection(self, cursor, user, vals, context=None):

        ar_obj = self.pool.get('mobile.ar.collection')
        str = "{" + vals + "}"
        str = str.replace("'',", "',")  # null
        str = str.replace(":',", ":'',")  # due to order_id
        str = str.replace("}{", "}|{")
        str = str.replace(":'}{", ":''}")    
        new_arr = str.split('|')
        result = []
        for data in new_arr:
            x = ast.literal_eval(data)
            result.append(x)
        ar_collection = []
        for r in result:
            print "length", len(r)
            ar_collection.append(r)  
        if ar_collection:
            for ar in ar_collection:            
                cursor.execute('select origin from account_invoice where number=%s', (ar['ref_no'].replace('\\', ""),))
                origin = cursor.fetchone()
                if origin:
                    origin = origin[0]
                else:
                    origin = None
                    
                ar_result = {
                    'customer_code':ar['customer_code'],
                    'partner_id':ar['partner_id'],
                    'credit_limit':ar['credit_limit'],
                    'date':ar['date'] ,
                    'tablet_id':ar['tablet_id'],
                    'void_flag':ar['void_flag'],
                    'payment_amount':ar['payment_amount'],
                    'so_amount':ar['so_amount'],
                    'balance':ar['balance'],
                    'ref_no':ar['ref_no'].replace('\\', ""),
                    'so_ref':origin,
                    'sale_team_id':ar['sale_team_id'],
                    'user_id':ar['user_id'],
                    'state':'draft',
                }
                ar_obj.create(cursor, user, ar_result, context=context)
        return True
    
    def create_sale_rental(self, cursor, user, vals, context=None):
         try:
            rental_obj = self.pool.get('sales.rental')
            str = "{" + vals + "}"
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            rental_collection = []
            for r in result:
                rental_collection.append(r)  
            if rental_collection:
                for ar in rental_collection:            
                    cursor.execute('select id From res_partner where customer_code = %s ', (ar['partner_id'],))
                    data = cursor.fetchall()
                    if data:
                        partner_id = data[0][0]
                    else:
                        partner_id = None
                    
                    rental_result = {
                    
                        'partner_id':partner_id,
                        'from_date':ar['from_date'],
                        'date':ar['date'] ,
                        'to_date':ar['to_date'],
                        'image':ar['image'],
                        'company_id':ar['company_id'],
                        'monthy_amt':ar['monthy_amt'],
                        'month':'month',
                        'latitude':ar['latitude'],
                        'longitude':ar['longitude'],
                        'address':ar['address'],
                        'month':ar['month'],
                        'name':ar['name'],
                        'total_amt':ar['total_amt'],
                    }
                    rental_obj.create(cursor, user, rental_result, context=context)
            return True
         except Exception, e:
            print 'False'
            return False
    def get_credit_notes(self, cr, uid, sale_team_id , context=None, **kwargs):
        cr.execute('''            
                  select ac.id,ac.description,ac.name,ac.used_date,
                    ac.issued_date,ac.terms_and_conditions,ac.amount,ac.so_no,
                    ac.m_status,ac.customer_id,ac.type,ac.sale_team_id,res.name,res.customer_code,ac.ref_no
                 from account_creditnote ac,res_partner res
                   where ac.customer_id = res.id
                   and ac.m_status = 'new'
                   and  ac.sale_team_id = %s
         ''', (sale_team_id,))
        datas = cr.fetchall()
        cr.execute
        return datas
    
    def udpate_credit_notes_issue_status(self, cr, uid, sale_team_id , context=None, **kwargs):
        try:
            cr.execute('''update account_creditnote set m_Status='issued' where
                        sale_team_id = %s and m_status ='new'
             ''', (sale_team_id,))
            return True
        except Exception, e:
            return False
    
    def create_partner_photo(self, cursor, user, vals, context=None):
        
        try:
            print 'vals', vals
            customer_photo_obj = self.pool.get('partner.photo')
            str = "{" + vals + "}"    
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")        
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            customer_photo = []
            for r in result:  
                customer_photo.append(r)
            if customer_photo:
                for vs in customer_photo:
                    code = vs['customer_code']                                
                    
                    result = {
                        'customer_code':vs['customer_code'],
                        'customer_id':vs['customer_id'],
                        'comment':vs['comment'],
                        'image_one':vs['image_one'].replace('\\', ""),
                        'image_two':vs['image_two'].replace('\\', ""),
                        'image_three':vs['image_three'].replace('\\', ""),
                        'image_four':vs['image_four'].replace('\\', ""),
                        'image_five':vs['image_five'].replace('\\', "")
                    }
                    customer_photo_obj.create(cursor, user, result, context=context)                
                                                                  
                    # For Custoemr Photo temp table to Res Parnter Table for Appear
                    cursor.execute('''select customer_code,image_one,image_two,image_three,image_four,
                            image_five,comment From partner_photo where customer_code = %s''', (code,))
                    data = cursor.fetchall()
                    for r in data:
                        code = r[0]
                        print 'customer id', code
                        cursor.execute('''update res_partner set image_one = %s, image_two = %s,
                        image_three = %s, image_four = %s, image_five = %s, comment = %s where customer_code = %s'''
                        , (r[1], r[2], r[3], r[4], r[5]
                        , r[6], code,))
                        cursor.execute('''delete from partner_photo where customer_code = %s''', (vs['customer_code'],))
            return True
        except Exception, e:
            print e
            return False
                
    def udpate_credit_notes_used_status(self, cr, uid, sale_team_id , usedList, context=None, **kwargs):
        try:
            crnote = tuple(usedList)
            note_order_obj = self.pool.get('account.creditnote')
            list_val = None
            list_val = note_order_obj.search(cr, uid, [('sale_team_id', '=', sale_team_id), ('m_status', '=', 'issued'), ('name', 'in', usedList)])            
            print'credit id', list_val
            for note_id in list_val:
                print'Note id', note_id
                cr.execute("""update account_creditnote set m_status ='used' where id = %s""", (note_id,))
            return True
        except Exception, e:
            return False
    
    def get_branch_datas(self, cr, uid , context=None):        
        cr.execute('''select id,name,branch_code from res_branch where active = true''')
        datas = cr.fetchall()        
        return datas
    
    def get_sale_channel(self, cr, uid , context=None):        
        cr.execute('''select id,name from sale_channel''')
        datas = cr.fetchall()        
        return datas
        
    def get_payment_term(self, cr, uid , context=None):        
        cr.execute('''select id,name from account_payment_term where active = true''')
        datas = cr.fetchall()        
        return datas
    
    def get_promo_sale_channel(self, cr, uid , context=None):        
        cr.execute('''select promo_id,sale_channel_id from promo_sale_channel_rel''')
        datas = cr.fetchall()        
        return datas    
    
    def get_sale_team_channel(self, cr, uid, sale_team_id , context=None, **kwargs):    
        cr.execute("""select sale_team_id,sale_channel_id from sale_team_channel_rel
                        where sale_team_id = %s """, (sale_team_id,))                
        datas = cr.fetchall()
        return datas
    
    def get_uom(self, cr, uid, context=None, **kwargs):    
        cr.execute("""select id,name,floor(1/factor) as ratio from product_uom where active = true""")
        datas = cr.fetchall()
        print 'Product UOM', datas
        return datas
    
    def get_asset_type(self, cr, uid, context=None, **kwargs):    
        cr.execute("""select id,name from asset_type""")
        datas = cr.fetchall()        
        return datas
    
    def get_assets(self, cr, uid, context=None, **kwargs):    
        cr.execute("""select A.id,A.name,A.partner_id,substring(encode(image::bytea, 'hex'),1,5) as image
                    ,A.qty,A.date,B.name,A.type 
                    from res_partner_asset A, asset_type B
                    where A.asset_type = B.id""")
        datas = cr.fetchall()
        return datas
        
    # Get Pending Delivery
    def get_delivery_datas(self, cr, uid, saleTeamId, soList, context=None, **kwargs):
        
        sale_order_obj = self.pool.get('sale.order')
        list_val = None
        list_val = sale_order_obj.search(cr, uid, [('pre_order', '=', True), ('is_generate', '=', True), ('delivery_id', '=', saleTeamId), ('shipped', '=', False), ('invoiced', '=', False) , ('tb_ref_no', 'not in', soList)], context=context)
        print 'list_val', list_val
        list = []
        try:
            if list_val:
                for So_id in list_val:
                    print 'Sale Order Id', So_id
                    cr.execute('''select so.id,so.date_order,so.partner_id,so.amount_tax,so.amount_untaxed,
                    so.payment_term,so.company_id,so.pricelist_id,so.user_id,so.amount_total,so.name as invoice_no,
                    so.warehouse_id,so.shipped,so.sale_plan_day_id,so.sale_plan_name,so.so_longitude,so.payment_type,
                    so.due_date,so.sale_plan_trip_id,so.so_latitude,so.customer_code,so.name as so_refNo,so.total_dis,so.deduct_amt,so.coupon_code,
                    so.invoiced,so.branch_id,so.delivery_remark ,team.name,so.payment_term,so.due_date
                    from sale_order so, crm_case_section team                                    
                    where so.id= %s
                    and  team.id = so.section_id''', (So_id,))
                    result = cr.fetchall()
                    print 'Result Sale Order', result
                    list.append(result)
                    print' list', list
            return list
        except Exception, e:
            return False
    
    def get_delivery_line_datas(self, cr, uid, so_ids, context=None, **kwargs):
        print 'So_ids', so_ids
        order_ids = so_ids
        so_line_obj = self.pool.get('sale.order.line')
        list_val = None
        list_val = so_line_obj.search(cr, uid, [('order_id', 'in', order_ids)])
        print 'list_val', list_val
        list = []
        if list_val:
            for val in list_val:
                cr.execute('''select so.id,so.product_id,so.product_uom_qty,so.product_uom,so.price_unit,so.order_id,
                            so.discount,so.discount_amt ,pp.sequence
                            from sale_order_line so,product_product pp
                            where so.id = %s 
                            and so.product_id = pp.id''', (val,))
                result = cr.fetchall()
                list.append(result)
                print' list', list
        return list
    
    def update_deliver_sale_order(self, cr, uid, saleorderList, context=None):
         
            context = {'lang':'en_US', 'params':{'action':458}, 'tz': 'Asia/Rangoon', 'uid': 1}
            soObj = self.pool.get('sale.order')        
            invObj = self.pool.get("sale.advance.payment.inv")
            invoiceObj = self.pool.get('account.invoice')                
            stockPickingObj = self.pool.get('stock.picking')
            stockDetailObj = self.pool.get('stock.transfer_details')        
            partner_obj = self.pool.get('res.partner')
            
            str = "{" + saleorderList + "}"    
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:            
                x = ast.literal_eval(data)                
                result.append(x)
            deliver_data = []
            for r in result:
                deliver_data.append(r)  
            if deliver_data:
                
                for deli in deliver_data:       
                    print 'Miss', deli['miss'], deli
                    so_ref_no = deli['so_refNo'].replace('\\','').replace('\\','')          
                    print       'so_ref_noso_ref_no',so_ref_no
                    if deli['miss'] == 't':
                        cr.execute('update sale_order set is_generate = false, due_date = %s where name=%s', (deli['due_date'], so_ref_no,))
                        cr.execute('select tb_ref_no from sale_order where name=%s',( so_ref_no,))
                        ref_no=cr.fetchone()[0]
                        cr.execute("update pre_sale_order set void_flag = 'voided' where name=%s", ( ref_no,))
                    else:                            
                        So_id = soObj.search(cr, uid, [('pre_order', '=', True), ('shipped', '=', False), ('invoiced', '=', False)
                                                       , ('name', '=', so_ref_no)], context=context)
                        if So_id:
                            solist = So_id                               
                            cr.execute('select branch_id,section_id,delivery_remark from sale_order where name=%s', (so_ref_no,))
                            data = cr.fetchone()
                            if data:
                                branch_id = data[0]
                                section_id = data[1]
                                delivery_remark = data[2]

                            cr.execute('select delivery_team_id from crm_case_section where id=%s', (section_id,))
                            delivery = cr.fetchone()
                            if delivery:
                                delivery_team_id = delivery[0]
                            else:
                                delivery_team_id = None
                            
                            # For DO
                            stockViewResult = soObj.action_view_delivery(cr, uid, So_id, context=context)    
                            if stockViewResult:
                                # stockViewResult is form result
                                # stocking id =>stockViewResult['res_id']
                                # click force_assign
                                stockPickingObj.force_assign(cr, uid, stockViewResult['res_id'], context=context)
                                # transfer
                                # call the transfer wizard
                                # change list
                                pickList = []
                                pickList.append(stockViewResult['res_id'])
                                wizResult = stockPickingObj.do_enter_transfer_details(cr, uid, pickList, context=context)
                                # pop up wizard form => wizResult
                                detailObj = stockDetailObj.browse(cr, uid, wizResult['res_id'], context=context)
                                if detailObj:
                                    detailObj.do_detailed_transfer()    
                                print 'testing---------------',
                            # Create Invoice
                            print 'Context', context
                            invoice_id = self.create_invoices(cr, uid, solist, context=context)
                            print ' invoice_id', invoice_id
                            # id update partner form (temporay)
#                             partner_data = invoiceObj.browse(cr, uid, invoice_id, context=context)
#                             partner_id=partner_data.partner_id.id
#                             partner_obj.write(cr,uid,partner_id,{'property_account_receivable':629}, context)
#                             partner = partner_obj.browse(cr, uid, partner_id, context=context)
#                             account_id=partner.property_account_receivable.id
#                             invoiceObj.write(cr,uid,invoice_id,{'account_id':account_id}, context)
                            cr.execute('update account_invoice set date_invoice = now()::date , branch_id =%s ,payment_type=%s,delivery_remark =%s ,section_id=%s,user_id=%s, payment_term = %s where id =%s',(branch_id, deli['payment_type'], delivery_remark, delivery_team_id, uid,deli['payment_term'],invoice_id))                                                
                                                        
                            invoiceObj.button_reset_taxes(cr, uid, [invoice_id], context=context)
                            if invoice_id:
                                invlist = []
                                invlist.append(invoice_id)
                                # call the api function
                                # invObj contain => account.invoice(1,) like that
                                print 'invoice_id', invoice_id
                                 
                                invObj = invoiceObj.browse(cr, uid, invlist, context=context)
                                
                                #                                                                                                                            
                                invObj.action_date_assign()
                                invObj.action_move_create()
                                invObj.action_number()
                                # validate invoice
                                invObj.invoice_validate()
                                # pre_order =True
                                invoiceObj.write(cr, uid, invoice_id, {'pre_order':True}, context)                                                                                                                             
                                                                        
            return True 
          
    def cancel_deliver_order(self, cr, uid, saleorderList, context=None):
         
            context = {'lang':'en_US', 'params':{'action':458}, 'tz': 'Asia/Rangoon', 'uid': 1}
            soObj = self.pool.get('sale.order')            
            
            str = "{" + saleorderList + "}"    
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:            
                x = ast.literal_eval(data)                
                result.append(x)
            deliver_data = []
            for r in result:
                deliver_data.append(r)  
            if deliver_data:
                
                for deli in deliver_data:            
                    print 'Journal ID', deli['journal_id']
                    print 'Payment Type', deli['payment_type']
                    print 'So Ref No', deli['so_refNo']
                    so_ref_no = deli['so_refNo'].replace('||','')
                    So_id = soObj.search(cr, uid, [('pre_order', '=', True), ('shipped', '=', False), ('invoiced', '=', False)
                                                   , ('name', '=', so_ref_no)], context=context)
                    if So_id:
                        print 'Sale Order Id', So_id[0]
                        cr.execute('''update sale_order set state ='cancel' where id = %s ''', (So_id[0],))
                        cr.execute('select tb_ref_no from sale_order where id=%s',(So_id[0],))
                        ref_no=cr.fetchone()[0]
                        cr.execute("update pre_sale_order set void_flag = 'voided' where name=%s", ( ref_no,))                                                                                                                                                                                                                            
            return True  
                   
    def create_mobile_stock_return(self, cursor, user, vals, context=None):
        try :
            stock_return_obj = self.pool.get('stock.return.mobile')
            stock_return_line_obj = self.pool.get('stock.return.mobile.line')
            str = "{" + vals + "}"
            str = str.replace(":''", ":'")  # change Order_id
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace(":'}", ":''}")
            str = str.replace("}{", "}|{")
            
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            stock = []
            stock_line = []
            for r in result:
                print "length", len(r)
                if len(r) >= 6:
                    stock_line.append(r)                   
                else:
                    stock.append(r)
            
            if stock:
                for sr in stock:
                    cursor.execute('select id from stock_return_mobile where user_id = %s and return_date=%s ', (user, sr['return_date'],))
                    data = cursor.fetchall()
                    if data:
                        stock_return_id = data[0][0]
                        cursor.execute('delete from stock_return_mobile where id = %s ', (stock_return_id,))
                        cursor.execute('delete from stock_return_mobile_line where line_id = %s ', (stock_return_id,))
                    cursor.execute("select vehicle_id from crm_case_section where id=%s", (sr['sale_team_id'],))
                    vehicle_id = cursor.fetchone()
                    if vehicle_id:
                        vehicle_id = vehicle_id[0]
                    else:
                        vehicle_id = None
                    print 'vehicle_id', vehicle_id
                    mso_result = {
                        'sale_team_id':sr['sale_team_id'],
                        'return_date':sr['return_date'],
                        'company_id':sr['company_id'],
                        'branch_id':sr['branch_id'],
                        'user_id':user,
                        'vehicle_id':vehicle_id,

                    }
                    stock_id = stock_return_obj.create(cursor, user, mso_result, context=context)                  
                    for srl in stock_line:  # return_quantity=  float(srl['return_quantity']) - (float(srl['sale_quantity'])+float(srl['foc_quantity'] ))          
                            return_quantity = srl['return_quantity']
                            mso_line_res = {                                                            
                                  'line_id':stock_id,
                                  'return_quantity':return_quantity,
                                  'sale_quantity':srl['sale_quantity'],
                                  'product_id':srl['product_id'],
                                  'product_uom':srl['product_uom'],
                                  'foc_quantity':srl['foc_quantity'],
                            }
                            stock_return_line_obj.create(cursor, user, mso_line_res, context=context)
            print 'True'
            return True       
        except Exception, e:
            print 'False'
            return False  
    # RFI
    def create_stock_request_from_mobile(self, cursor, user, vals, context=None):
        print 'vals', vals
        try : 
            stock_request_obj = self.pool.get('stock.requisition')
            stock_request_line_obj = self.pool.get('stock.requisition.line')
            str = "{" + vals + "}"
            str = str.replace(":''", ":'")  # change Order_id
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace(":'}", ":''}")
            str = str.replace("}{", "}|{")
            
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            stock = []
            stock_line = []
            for r in result:
                print "length", len(r)
                if len(r) >= 7:
                    stock.append(r)                                    
                else:
                    stock_line.append(r)
            
            if stock:
                for sr in stock:                                    
                    cursor.execute('select vehicle_id,location_id,issue_location_id,delivery_team_id,receiver from crm_case_section where id = %s ', (sr['sale_team_id'],))
                    data = cursor.fetchall()
                    if data:
                        vehcle_no = data[0][0]
                        from_location_id = data[0][1]
                        to_location_id = data[0][2]
                        delivery_id = data[0][3]             
                        receiver=data[0][4]           
                    else:
                        vehcle_no = None
                        from_location_id = None
                        to_location_id = None
                        delivery_id = None          
                        receiver=None
                    
                    mso_result = {
                        'request_date':sr['request_date'],
                        'request_by':sr['request_by'],
                        'issue_date':sr['issue_date'] ,
                         's_issue_date':sr['issue_date'] ,
                        'state': 'draft',
                        'issue_to':receiver,
                        'company_id':sr['company_id'],
                        'branch_id':sr['branch_id'],
                        'vehicle_id':vehcle_no,
                        'from_location_id':from_location_id,
                        'to_location_id':to_location_id,
                        'sale_team_id':delivery_id,
                    }
                    stock_id = stock_request_obj.create(cursor, user, mso_result, context=context)
                    
                    for srl in stock_line:
                        if (sr['rfi_no'] == srl['rfi_no']):
                            cursor.execute('select a.uom_ratio,a.uom_id from product_template a, product_product b where a.id = b.product_tmpl_id and b.id = %s ', (srl['product_id'],))
                            data = cursor.fetchall()
                            if data:
                                packing_unit = data[0][0]
                                small_uom_id = data[0][1]
                            else:
                                packing_unit = None
                                small_uom_id = None

                            req_quantity = int(srl['req_quantity'])
                           
                            cursor.execute('select  SUM(COALESCE(qty,0)) qty from stock_quant where location_id=%s and product_id=%s and qty >0 group by product_id', (from_location_id, srl['product_id'],))
                            qty_on_hand = cursor.fetchone()
                            if qty_on_hand:
                                qty_on_hand = qty_on_hand[0]
                            else:
                                qty_on_hand = 0               

                            mso_line_res = {                                                            
                                      'line_id':stock_id,
                                      'remark':srl['remark'],
                                      'req_quantity':req_quantity,
                                      'product_id':int(srl['product_id']),
                                      'product_uom':small_uom_id,
                                      'uom_ratio':packing_unit ,

                                      'qty_on_hand':qty_on_hand,
                                      }
                            stock_request_line_obj.create(cursor, user, mso_line_res, context=context)
            print 'True'
            return True       
        except Exception, e:
            print 'False'
            return False
    
    def get_promos_outlet(self, cr, uid, context=None, **kwargs):    
        cr.execute("""select promos_rules_id,outlettype_id from promos_rules_outlettype_rel""")
        datas = cr.fetchall()        
        return datas
    
    def get_promos_branch(self, cr, uid, context=None, **kwargs):    
        cr.execute("""select promos_rules_id,res_branch_id from promos_rules_res_branch_rel""")
        datas = cr.fetchall()        
        return datas
    
    def get_promos_partner(self, cr, uid, context=None, **kwargs):    
        cr.execute("""select promos_rules_id,res_partner_id from promos_rules_res_partner_rel""")
        datas = cr.fetchall()        
        return datas
    
    def get_account_journal(self, cr, uid, context=None, **kwargs):    
        cr.execute("""select id,name from account_journal where is_tablet = true""")
        datas = cr.fetchall()        
        return datas
        
    def get_promo_product(self, cr, uid, context=None, **kwargs):    
        cr.execute('''select promos_rules_id,product_id from promos_rules_product_rel''')
        datas = cr.fetchall()        
        return datas
    
    def stock_deliver(self, cr, uid, ids, soId, context=None):
        sale_obj = self.pool.get('sale.order')
        if soId:
            sale_id = sale_obj.browse(cr, uid, soId, context)
            procurement_group_id = stock_picking_id = None
            cr.execute(""" select id from procurement_group where name = %s """, (sale_id.name,))
            data = cr.fetchall()
            if data:
                try:
                    procurement_group_id = data[0][0]
                except Exception, e:
                    procurement_group_id = data[0]    
            if procurement_group_id:
                procurement_group = self.pool.get('procurement.group').browse(cr, uid, procurement_group_id, context)        
            if procurement_group:
                cr.execute(""" select id from stock_picking where group_id =%s and state not in ('draft','cancel','done') """, (procurement_group.id,))
                data = cr.fetchall()
                if data:
                    try:
                        stock_picking_id = data[0][0]
                    except Exception, e:
                        stock_picking_id = data[0]
            if stock_picking_id:
                stock_picking = self.pool.get('stock.picking').browse(cr, uid, stock_picking_id, context)
            else:
                raise osv.except_osv(_('No More Stock Receive!'), _("There no stock receipt for Incoming Stock ."))
                return False
            if stock_picking:
                cr.execute(""" select id from stock_move where picking_id =%s """ , (stock_picking.id,))
                data = cr.fetchall()
                if data:
                    try:
                        move_list = data[0]
                    except Exception, e:
                        move_list = data
                if move_list:
                    result = {}
                    result = self.pool.get('stock.move').read(cr, uid, move_list[0], ['product_uom_qty'], context)
                    total_qty = result['product_uom_qty']
                if total_qty > 0:
                    print 'Stock Received Successful'
                    # first confirm the original picking, original qty - actual qty
                    cr.execute(""" update stock_move set product_uom_qty = %s where picking_id = %s """, (total_qty, stock_picking.id,))
                    move_id = None
                    cr.execute(""" select id from stock_move where picking_id = %s """ , (stock_picking.id,))
                    data = cr.fetchall()
                    if data:
                        try:
                            move_id = data[0][0]
                        except Exception, e:
                            move_id = data[0]
                    if move_id:
                        self.pool.get('stock.move').action_done(cr, uid, move_id, context)
                    self.write(cr, uid, ids, {'state':'done'}, context=None)                    
        return True
    
    def create_sale_order_payment(self, cursor, user, vals, context=None):
        try:
            rental_obj = self.pool.get('customer.payment')
            str = "{" + vals + "}"
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            rental_collection = []
            for r in result:
                rental_collection.append(r)  
            if rental_collection:
                for ar in rental_collection:
                    cursor.execute('select id from mobile_sale_order where name = %s ', (ar['payment_id'],))
                    data = cursor.fetchall()
                    if data:
                        so_id = data[0][0]
                    else:
                        so_id = None
                    
                    cursor.execute('select id from res_partner where customer_code = %s ', (ar['partner_id'],))
                    data = cursor.fetchall()
                    if data:
                        parnter_id = data[0][0]
                    else:
                        parnter_id = None

                    amount = ar['amount']
                    cursor.execute("select replace(%s, ',', '')::float as amount", (amount,))
                    amount_data = cursor.fetchone()[0]
                    amount = amount_data
                    rental_result = {                    
                        'payment_id':so_id,
                        'journal_id':ar['journal_id'],
                        'amount':amount,
                        'date':ar['date'],
                        'notes':ar['notes'],
                        'cheque_no':ar['cheque_no'],
                        'partner_id':parnter_id,
                        'sale_team_id':ar['sale_team_id'],
                        'payment_code':ar['payment_code'],
                    }
                    rental_obj.create(cursor, user, rental_result, context=context)
            return True
        except Exception, e:
            print 'False'
            return False
        
    def create_pre_order_payment(self, cursor, user, vals, context=None):
        try:
            rental_obj = self.pool.get('customer.payment')
            str = "{" + vals + "}"
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
#             rental_collection = []
#             for r in result:
#                 rental_collection.append(r)  
            if result:
                for ar in result:
                    payment_id  = ar['payment_id'].replace('\\','').replace('\\','')           
                    cursor.execute('select tb_ref_no from sale_order where name = %s ', (payment_id,))
                    data = cursor.fetchall()
                    if data:
                        pre_no = data[0][0]
                    else:
                        pre_no = None
                    
                    cursor.execute('select id from pre_sale_order where name = %s ', (pre_no,))
                    data = cursor.fetchall()
                    if data:
                        so_id = data[0][0]
                    else:
                        so_id = None
                    
                    rental_result = {                    
                        'pre_order_id':so_id,
                        'journal_id':ar['journal_id'],
                        'amount':ar['amount'],
                        'date':ar['date'],
                        'notes':payment_id,
                        'cheque_no':ar['cheque_no'],
                        'partner_id':ar['partner_id'],
                        'sale_team_id':ar['sale_team_id'],
                        'payment_code':ar['payment_code'],
                    }
                    rental_obj.create(cursor, user, rental_result, context=context)
            return True
        except Exception, e:
            print 'False'
            return False  
    
    def get_country(self, cr, uid , context=None):        
        cr.execute('''select id,code,name from res_country where id between 146 and 160''')
        datas = cr.fetchall()        
        return datas
    def get_division_state(self, cr, uid , context=None):        
        cr.execute('''select id,name from res_country_state''')
        datas = cr.fetchall()        
        return datas
    
    def get_city(self, cr, uid , context=None):        
        cr.execute('''select id,code,name,state_id from res_city''')
        datas = cr.fetchall()        
        return datas
    
    def get_township(self, cr, uid , context=None):        
        cr.execute('''select id,code,name,city from res_township''')
        datas = cr.fetchall()        
        return datas

    def get_outlet_type(self, cr, uid , context=None):        
        cr.execute('''select id,name from outlettype_outlettype''')
        datas = cr.fetchall()        
        return datas
    
    def get_sale_demarcation(self, cr, uid , context=None):        
        cr.execute('''select id,name from sale_demarcation''')
        datas = cr.fetchall()        
        return datas
     
    def get_sale_class(self, cr, uid , context=None):        
        cr.execute('''select id,name from sale_class''')
        datas = cr.fetchall()        
        return datas
    
    def get_frequency(self, cr, uid , context=None):        
        cr.execute('''select id,name from plan_frequency''')
        datas = cr.fetchall()        
        return datas
    # Create New Customer from Tablet by kzo
    def create_new_customer(self, cursor, user, vals, context=None):
        try:
            partner_obj = self.pool.get('res.partner')
            parnter_tag_obj = self.pool.get('res.partner.res.partner.category.rel')
            str = "{" + vals + "}"
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            new_partner = []
            for r in result:
                new_partner.append(r)  
            if new_partner:
                for partner in new_partner:
                    chiller = False;
                    if 'chiller' in partner:
                        chiller = partner['chiller']
                    partner_result = {                 
                        'country_id':partner['country_id'],
                        'state_id':partner['state_id'],
                        'city':partner['city'],
                        'street':partner['street'],
                        'street2':partner['street2'],
                        'display_name':partner['name'],
                        'name':partner['name'],
                        'email':partner['email'],
                        'is_company':True,
                        'customer':True,
                        'employee':False,
                        'phone':partner['phone'],
                        'mobile':partner['mobile'],
                        'notify_email':'always',
                        'township':partner['township'],
                        'partner_latitude':partner['partner_latitude'],
                        'partner_longitude':partner['partner_longitude'],
                        'branch_id':partner['branch_id'],
                        'outlet_type':partner['outlet_type'],
                        'customer_code':partner['customer_code'],
                        'class_id':partner['class_id'],
                        'mobile_customer':True,
                        'pricelist_id':partner['pricelist_id'],
                        'chiller':chiller,
                        'unit':partner['unit'],
                        'image':partner['image'],
                        'sales_channel':partner['sales_channel'],
                        'temp_customer':partner['temp_customer'],
                        'frequency_id':partner['frequency_id'],
                        'section_id':partner['section_id'],
                    }
                    partner_id = partner_obj.create(cursor, user, partner_result, context=context)                    
                    
                    cursor.execute(''' insert into res_partner_res_partner_category_rel(category_id,partner_id) 
                    values(2,%s)''', (partner_id,))
                    
            return partner_id
        except Exception, e:
            print 'False'
            return 0
    
    # GET Pending DELIVER CUSTOMER
    def get_deliver_customer(self, cr, uid, saleTeamId, parnterList, context=None, **kwargs):    
        
        partner_list = None
        parnterList = str(tuple(parnterList))
        parnterList = eval(parnterList)
        print 'Param Customer List', parnterList
        
        if parnterList:
                cr.execute('''select PARTNER_ID from sale_order WHERE pre_order = TRUE AND delivery_id = %s 
                AND shipped = False
                AND invoiced = False
                AND PARTNER_ID NOT IN %s''', (saleTeamId, parnterList,))
            
        else:
            cr.execute('''select PARTNER_ID from sale_order 
                WHERE pre_order = TRUE 
                AND delivery_id = %s 
                AND shipped = False
                AND invoiced = False
                ''', (saleTeamId,))
            
        data = cr.fetchall()
        if data:
            partner_list = data
        else:
            partner_list = None
        

        result = []
        try:
            if partner_list: 
                partner_list = str(tuple(partner_list))
                partner_list = eval(partner_list)
                print 'list_val', partner_list           
                cr.execute('''select A.id,A.name,A.image,A.is_company, A.image_small,replace(A.street,',',';') street,replace(A.street2,',',';') street2,A.city,A.website,
                     replace(A.phone,',',';') phone,A.township,replace(A.mobile,',',';') mobile,A.email,A.company_id,A.customer, 
                     A.customer_code,A.mobile_customer,A.shop_name ,
                     A.address,
                     A.zip,A.state_name,A.partner_latitude,A.partner_longitude,null,A.image_medium,A.credit_limit,
                     A.credit_allow,A.sales_channel,A.branch_id,A.pricelist_id,A.payment_term_id,A.outlet_type ,
                     A.city_id,A.township_id,A.country_id,A.state_id,A.unit,A.class_id,A.chiller,A.frequency_id,A.temp_customer,
                     A.is_consignment,A.hamper,A.is_bank,A.is_cheque
                     from (

                     select RP.id,RP.name,'' as image,RP.is_company,null,
                     '' as image_small,RP.street,RP.street2,RC.name as city,RP.website,
                     RP.phone,RT.name as township,RP.mobile,RP.email,RP.company_id,RP.customer, 
                     RP.customer_code,RP.mobile_customer,OT.name as shop_name,RP.address,RP.zip ,RP.partner_latitude,RP.partner_longitude,RS.name as state_name,
                     substring(replace(cast(RP.image_medium as text),'/',''),1,5) as image_medium,RP.credit_limit,RP.credit_allow,
                     RP.sales_channel,RP.branch_id,RP.pricelist_id,RP.payment_term_id,RP.outlet_type,RP.city as city_id,RP.township as township_id,
                     RP.country_id,RP.state_id,RP.unit,RP.class_id,RP.chiller,RP.frequency_id,RP.temp_customer,RP.is_consignment,
                     RP.hamper,RP.is_bank,RP.is_cheque

                     from  res_partner RP ,res_country_state RS, res_city RC,res_township RT,
                             outlettype_outlettype OT
                                            where RS.id = RP.state_id
                                            and RP.township =RT.id
                                            and RP.city = RC.id
                                            and RP.outlet_type = OT.id
                                            and RP.id in %s                                                                                
                                            order by RP.name                                       
                        )A 
                        where A.customer_code is not null
                            ''', (partner_list ,))
                result = cr.fetchall()
            return result
        except Exception, e:
            return False
    
    def get_credit_invoice(self, cr, uid, partner_list, branch_id , invoiceList, context=None):    
        data_line = []
        if partner_list:
            partner_list = str(tuple(partner_list))
            partner_list = eval(partner_list)
            
            invoiceList = str(tuple(invoiceList))
            invoiceList = eval(invoiceList)
            if invoiceList:        
                cr.execute(''' 
                    select inv.id,inv.number,inv.partner_id,rp.name customer_name,
                           rp.customer_code customer_code,inv.origin so_no,inv.date_invoice,
                           inv.amount_total,inv.residual balance,inv.payment_type,
                           inv.journal_id,crm.name,inv.date_due
                    from account_invoice inv, res_partner rp, crm_case_section crm
                    where inv.payment_type='credit' 
                    and inv.state='open' 
                    and inv.type = 'out_invoice'
                    and inv.branch_id = %s 
                    and residual > 0
                    and inv.partner_id = rp.id
                    and inv.section_id = crm.id
                    and inv.partner_id in %s
                    and inv.id NOT IN %s'''         
                    , (branch_id, partner_list, invoiceList ,))
            else:
                cr.execute(''' 
                    select inv.id,inv.number,inv.partner_id,rp.name customer_name,
                           rp.customer_code customer_code,inv.origin so_no,inv.date_invoice,
                           inv.amount_total,inv.residual balance,inv.payment_type,
                           inv.journal_id,crm.name,inv.date_due
                    from account_invoice inv, res_partner rp, crm_case_section crm
                    where inv.payment_type='credit' 
                    and inv.state='open' 
                    and inv.type = 'out_invoice'
                    and inv.branch_id = %s 
                    and residual > 0
                    and inv.partner_id = rp.id
                    and inv.section_id = crm.id
                    and inv.partner_id in %s
                    '''         
                    , (branch_id, partner_list,))            
            data_line = cr.fetchall()                    
        print 'data_lineeeeeeeeeeeeeee', data_line        
        return data_line
    
    def get_credit_invoice_line(self, cr, uid, partner_list, branch_id, invoiceList , context=None):    
        data_line = []
        if partner_list:
            partner_list = str(tuple(partner_list))
            partner_list = eval(partner_list)
            
            invoiceList = str(tuple(invoiceList))
            invoiceList = eval(invoiceList)
            
            if invoiceList:
                
                cr.execute(''' 
                    select  inv_line.id,inv_line.invoice_id,inv_line.product_id,pp.name_template, pp.default_code,
                            inv_line.quantity qty,inv_line.price_unit as price,inv_line.price_subtotal,
                            inv_line.discount,inv_line.discount_amt,inv_line.uos_id
                    from account_invoice inv, account_invoice_line inv_line, res_partner rp, product_product pp
                    where inv.id = inv_line.invoice_id
                    and inv.payment_type='credit' 
                    and inv.state='open' 
                    and inv.type = 'out_invoice'
                    and inv.branch_id = %s
                    and inv_line.product_id = pp.id
                    and residual > 0
                    and inv.partner_id = rp.id
                    and inv.partner_id in %s
                    and inv.id not in %s'''                       
                    , (branch_id, partner_list, invoiceList ,))
            else:
                cr.execute(''' 
                    select  inv_line.id,inv_line.invoice_id,inv_line.product_id,pp.name_template, pp.default_code,
                            inv_line.quantity qty,inv_line.price_unit as price,inv_line.price_subtotal,
                            inv_line.discount,inv_line.discount_amt,inv_line.uos_id
                    from account_invoice inv, account_invoice_line inv_line, res_partner rp, product_product pp
                    where inv.id = inv_line.invoice_id
                    and inv.payment_type='credit' 
                    and inv.state='open' 
                    and inv.type = 'out_invoice'
                    and inv.branch_id = %s
                    and inv_line.product_id = pp.id
                    and residual > 0
                    and inv.partner_id = rp.id
                    and inv.partner_id in %s
                    '''                       
                    , (branch_id, partner_list ,))
                      
            data_line = cr.fetchall()                    
        print 'data_lineeeeeeeeeeeeeee', data_line        
        return data_line
    
    def create_ar_collection_journal_payment(self, cursor, user, vals, context=None):
        try:
            rental_obj = self.pool.get('ar.payment')
            str = "{" + vals + "}"
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            if result:
                for ar in result:
                    ref_no = ar['payment_id'].replace('\\', "")
                    print 'Ref No', ref_no
                    cursor.execute('''select max(id) from mobile_ar_collection where ref_no = %s and write_date::date = now()::date ''', (ref_no,))
                    data = cursor.fetchall()
                    if data:
                        collection_id = data[0][0]
                    else:
                        collection_id = None                    
                    
                    rental_result = {                    
                        'collection_id':collection_id,
                        'journal_id':ar['journal_id'],
                        'amount':ar['amount'],
                        'date':ar['date'],
                        'notes':ar['notes'].replace('\\', ""),
                        'cheque_no':ar['cheque_no'].replace('\\', ""),
                        'partner_id':ar['partner_id'].replace('\\', ""),
                        'sale_team_id':ar['sale_team_id'].replace('\\', ""),
                        'payment_code':ar['payment_code'].replace('\\', ""),
                    }
                    rental_obj.create(cursor, user, rental_result, context=context)
            return True
        except Exception, e:
            print 'False'
            return False 

    def product_qty_in_stock(self, cr, uid, warehouse_id , context=None, **kwargs):
            cr.execute("""
            select product_id,qty_on_hand,main_group,name_template,price,sequence from
              (    
                select product.id as product_id,sum(qty) as qty_on_hand,product_temp.main_group as main_group,
                         product.name_template as name_template,product_temp.list_price as price,product.sequence
                         from  stock_quant quant, product_product product, product_template product_temp
                         where quant.location_id = %s
                         and quant.product_id = product.id
                         and product.product_tmpl_id = product_temp.id
                         and product.active = true
                         group by quant.product_id, main_group,name_template,product.id,price,product.sequence
            )A where qty_on_hand > 0  order by name_template
            """, (warehouse_id,))   
            datas = cr.fetchall()        
            return datas
    
    def create_customer_asset(self, cursor, user, vals, context=None):
        try:
            rental_obj = self.pool.get('res.partner.asset')
            str = "{" + vals + "}"
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:
                x = ast.literal_eval(data)
                result.append(x)
            if result:
                for ar in result:                            
                    cursor.execute('select id from asset_type where name = %s ', (ar['asset_type'],))
                    data = cursor.fetchall()
                    if data:
                        access_type_id = data[0][0]
                    else:
                        access_type_id = None                            
                        
                    rental_result = {                    
                        'partner_id':ar['partner_id'],
                        'qty':ar['qty'],
                        'image':ar['image'],
                        'date':ar['date'],
                        'name':ar['name'],
                        'asset_type':access_type_id,
                        'type':ar['type'],
                    }
                    rental_obj.create(cursor, user, rental_result, context=context)
            return True
        except Exception, e:
            print 'False'
            return False         
        
    def dayplan_is_update(self, cr, uid, team_id, late_date , context=None, **kwargs):
            
            flag = False
            lastdate = datetime.strptime(late_date, "%Y-%m-%d")
            print 'DateTime', lastdate
            cr.execute('select id from sale_plan_day where write_date > %s', (lastdate,))   
            datas = cr.fetchall()
            if datas:
                flag = True
            else:
                flag = False                     
            return flag
        
    def product_is_update(self, cr, uid, team_id, late_date , context=None, **kwargs):
            
            flag = False
            lastdate = datetime.strptime(late_date, "%Y-%m-%d")
            print 'DateTime', lastdate
            cr.execute('select id from product_template where write_date > %s', (lastdate,))   
            datas = cr.fetchall()
            if datas:
                flag = True
            else:
                flag = False                     
            return flag
        
    def customer_is_update(self, cr, uid, team_id, late_date , context=None, **kwargs):
            
            flag = False
            lastdate = datetime.strptime(late_date, "%Y-%m-%d")
            print 'DateTime', lastdate
            cr.execute(''' select id from res_partner A ,sale_team_customer_rel B
                    where A.id = B.partner_id
                    And A.write_date > %s
                    And B.sale_team_id = %s
            ''', (lastdate, team_id,))   
            datas = cr.fetchall()
            if datas:
                flag = True
            else:
                flag = False                     
            return flag
    
    def tripplan_is_update(self, cr, uid, team_id, late_date , context=None, **kwargs):
            
        try:
            flag = False
            lastdate = datetime.strptime(late_date, "%Y-%m-%d")
            print 'DateTime', lastdate
            cr.execute('''
            select p.id,p.date,p.sale_team,p.name,p.principal
             from sale_plan_trip p
            ,crm_case_section c,res_partner_sale_plan_trip_rel d, res_partner e
            where  p.sale_team=c.id
            and p.sale_team= %s
            and p.active = true 
            and p.id = d.sale_plan_trip_id
            and e.id = d.partner_id
            and (e.write_date > %s or p.write_date >  %s)
                ''', (team_id , lastdate, lastdate,))   
            datas = cr.fetchall()
            if datas:
                flag = True
            else:
                flag = False                   
            return flag
        except Exception, e:
            return False
    
    def res_partners_team(self, cr, uid, section_id, late_date, context=None, **kwargs):
        
        lastdate = datetime.strptime(late_date, "%Y-%m-%d")
        print 'DateTime', lastdate
        
        cr.execute('''                                
        select A.id,A.name,A.image,A.is_company, A.image_small,replace(A.street,',',';') street,replace(A.street2,',',';') street2,A.city,A.website,
                     replace(A.phone,',',';') phone,A.township,replace(A.mobile,',',';') mobile,A.email,A.company_id,A.customer, 
                     A.customer_code,A.mobile_customer,A.shop_name ,
                     A.address,
                     A.zip,A.state_name,A.partner_latitude,A.partner_longitude,null,A.image_medium,A.credit_limit,
                     A.credit_allow,A.sales_channel,A.branch_id,A.pricelist_id,A.payment_term_id,A.outlet_type ,
                     A.city_id,A.township_id,A.country_id,A.state_id,A.unit,A.class_id,A.chiller,A.frequency_id,A.temp_customer,
                     A.is_consignment,A.hamper,A.is_bank,A.is_cheque
                     
                     from (
                     select RP.id,RP.name,'' as image,RP.is_company,null,
                     '' as image_small,RP.street,RP.street2,RC.name as city,RP.website,
                     RP.phone,RT.name as township,RP.mobile,RP.email,RP.company_id,RP.customer, 
                     RP.customer_code,RP.mobile_customer,OT.name as shop_name,RP.address,RP.zip ,RP.partner_latitude,RP.partner_longitude,RS.name as state_name,
                     substring(replace(cast(RP.image_medium as text),'/',''),1,5) as image_medium,RP.credit_limit,RP.credit_allow,
                     RP.sales_channel,RP.branch_id,RP.pricelist_id,RP.payment_term_id,RP.outlet_type,RP.city as city_id,RP.township as township_id,
                     RP.country_id,RP.state_id,RP.unit,RP.class_id,RP.chiller,RP.frequency_id,RP.temp_customer,RP.is_consignment,RP.hamper,
                     RP.is_bank,RP.is_cheque
                     from sale_team_customer_rel ST ,outlettype_outlettype OT,
                                             res_partner RP ,res_country_state RS, res_city RC,res_township RT
                                            where ST.partner_id = RP.id 
                                            and  RS.id = RP.state_id
                                            and RP.township =RT.id
                                            and RP.city = RC.id
                                            and RP.active = true                                            
                                            and RP.outlet_type = OT.id                                            
                                            and ST.sale_team_id = %s                                   
                        )A 
                        where A.customer_code is not null
            ''', (section_id ,))
        datas = cr.fetchall()
        return datas

# kzo Eidt
    def res_partners_return_day(self, cr, uid, section_id, day_id, pull_date  , context=None, **kwargs):
    
        lastdate = datetime.strptime(pull_date, "%Y-%m-%d")
        print 'DateTime', lastdate
        cr.execute('''                    
                     select A.id,A.name,A.image,A.is_company, A.image_small,replace(A.street,',',';') street, replace(A.street2,',',';') street2,A.city,A.website,
                     replace(A.phone,',',';') phone,A.township, replace(A.mobile,',',';') mobile,A.email,A.company_id,A.customer, 
                     A.customer_code,A.mobile_customer,A.shop_name ,
                     A.address,
                     A.zip,A.state_name,A.partner_latitude,A.partner_longitude,A.sale_plan_day_id,A.image_medium,A.credit_limit,
                     A.credit_allow,A.sales_channel,A.branch_id,A.pricelist_id,A.payment_term_id,A.outlet_type ,
                     A.city_id,A.township_id,A.country_id,A.state_id,A.unit,A.class_id,A.chiller,A.frequency_id,A.temp_customer,
                     A.is_consignment,A.hamper,A.is_bank,A.is_cheque
                     from (
                     select RP.id,RP.name,'' as image,RP.is_company,RPS.sale_plan_day_id,
                     '' as image_small,RP.street,RP.street2,RC.name as city,RP.website,
                     RP.phone,RT.name as township,RP.mobile,RP.email,RP.company_id,RP.customer, 
                     RP.customer_code,RP.mobile_customer,OT.name as shop_name,RP.address,RP.zip ,RP.partner_latitude,RP.partner_longitude,RS.name as state_name,
                     substring(replace(cast(RP.image_medium as text),'/',''),1,5) as image_medium,RP.credit_limit,RP.credit_allow,
                     RP.sales_channel,RP.branch_id,RP.pricelist_id,RP.payment_term_id,RP.outlet_type,RP.city as city_id,RP.township as township_id,
                     RP.country_id,RP.state_id,RP.unit,RP.class_id,RP.chiller,RP.frequency_id,RP.temp_customer,RP.is_consignment,RP.hamper,
                     RP.is_bank,RP.is_cheque
                     from sale_plan_day SPD ,outlettype_outlettype OT,
                                            res_partner_sale_plan_day_rel RPS , res_partner RP ,res_country_state RS, res_city RC,res_township RT
                                            where SPD.id = RPS.sale_plan_day_id 
                                            and  RS.id = RP.state_id
                                            and RP.township =RT.id
                                            and RP.city = RC.id
                                            and RP.active = true
                                            and RP.outlet_type = OT.id
                                            and RPS.partner_id = RP.id 
                                            and SPD.sale_team = %s                                        
                                            and RPS.sale_plan_day_id = %s
                                            
                                                                            
                        )A 
                        where A.customer_code is not null
            ''', (section_id, day_id,))
        datas = cr.fetchall()
        return datas
# kzo Edit add Sale Plan Trip and Day ID
    def res_partners_return_trip(self, cr, uid, section_id, day_id , pull_date, context=None, **kwargs):
        
        lastdate = datetime.strptime(pull_date, "%Y-%m-%d")
        print 'DateTime', lastdate
        cr.execute('''        
                    select A.id,A.name,A.image,A.is_company,
                     A.image_small,replace(A.street,',',';') street,replace(A.street2,',',';') street2,A.city,A.website,
                     replace(A.phone,',',';') phone,A.township,A.mobile,A.email,A.company_id,A.customer, 
                     A.customer_code,A.mobile_customer,A.shop_name ,
                     A.address,
                     A.zip,A.state_name,A.partner_latitude,A.partner_longitude,A.sale_plan_trip_id,A.image_medium,
                     A.credit_limit,A.credit_allow,A.sales_channel,A.branch_id,A.pricelist_id,A.payment_term_id ,A.outlet_type,
                    A.city_id,A.township_id,A.country_id,A.state_id,A.unit,A.class_id,A.chiller,A.frequency_id,A.temp_customer,
                    A.is_consignment,A.hamper,A.is_bank,A.is_cheque
                      from (
                     select RP.id,RP.name,'' as image,RP.is_company,
                     '' as image_small,RP.street,RP.street2,RC.name as city,RP.website,
                     RP.phone,RT.name as township,RP.mobile,RP.email,RP.company_id,RP.customer, 
                     RP.customer_code,RP.mobile_customer,OT.name as shop_name ,RP.address,RPT.sale_plan_trip_id,
                     RP.zip ,RP.partner_latitude,RP.partner_longitude,RS.name as state_name
                      ,substring(replace(cast(RP.image_medium as text),'/',''),1,5) as image_medium ,RP.credit_limit,RP.credit_allow,
                     RP.sales_channel,RP.branch_id,RP.pricelist_id,RP.payment_term_id,RP.outlet_type,RP.city as city_id,RP.township as township_id,
                     RP.country_id,RP.state_id,RP.unit,RP.class_id,RP.chiller,RP.frequency_id,RP.temp_customer ,RP.is_consignment,RP.hamper,
                     RP.is_bank,RP.is_cheque
                     from sale_plan_trip SPT , res_partner_sale_plan_trip_rel RPT , res_partner RP ,res_country_state RS ,
                     res_city RC, res_township RT,outlettype_outlettype OT 
                     where SPT.id = RPT.sale_plan_trip_id 
                     and RPT.partner_id = RP.id 
                     and  RS.id = RP.state_id
                     and RP.outlet_type = OT.id
                     and  RP.city = RC.id
                     and RP.township = RT.id
                     and RP.active = true
                     and SPT.sale_team = %s
                     and RPT.sale_plan_trip_id = %s
                     
                        )A 
                    where A.customer_code is not null 
            ''', (section_id, day_id,))
        datas = cr.fetchall()
        return datas

    def get_promo_partner_category(self, cr, uid , context=None):        
        cr.execute('''select * from promotion_rule_category_rel''')
        datas = cr.fetchall()        
        return datas
    
    def get_partner_category_rel(self, cr, uid,section_id , context=None):        
        cr.execute('''select a.* from res_partner_res_partner_category_rel a,
                 res_partner_sale_plan_day_rel b
                 , sale_plan_day p
                where a.partner_id = b.partner_id
                and b.sale_plan_day_id = p.id
                and p.sale_team = %s
                ''',(section_id,))
        datas = cr.fetchall()        
        return datas
    
    def get_monthly_promotion_history(self, cr, uid, section_id , context=None, **kwargs):
            cr.execute("""
            select promotion_id,date, partner_id,section_id from sales_promotion_history where section_id = %s
            and  date between date_trunc('month', current_date)::date
            and  DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'  - INTERVAL '1 day' 
            """, (section_id,))   
            datas = cr.fetchall()        
            return datas
    
    def create_monthly_promotion_history(self, cursor, user, vals, context=None):
                    
            promo_his_obj = self.pool.get('sales.promotion.history')
            str = "{" + vals + "}"    
            str = str.replace("'',", "',")  # null
            str = str.replace(":',", ":'',")  # due to order_id
            str = str.replace("}{", "}|{")
            str = str.replace(":'}{", ":''}")
            new_arr = str.split('|')
            result = []
            for data in new_arr:            
                x = ast.literal_eval(data)                
                result.append(x)
            month_history = []
            for r in result:                
                month_history.append(r)  
            if month_history:
                for pro in month_history:
                                                
                    pro_his = {
                        'section_id':pro['section_id'],
                        'partner_id':pro['partner_id'],
                        'promotion_id':pro['promotion_id'],
                        'date':pro['date'],
                        'user_id':pro['user_id'],        
                    }
                    promo_his_obj.create(cursor, user, pro_his, context=context)
            return True
    
mobile_sale_order()

class mobile_sale_order_line(osv.osv):
    
    _name = "mobile.sale.order.line"
    _description = "Mobile Sales Order"
    
    def _get_uom_from_product(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for rec in self.browse(cr, uid, ids, context=context):
            result[rec.id] = rec.product_id.uom_id
        return result    
    
    _columns = {
        'product_id':fields.many2one('product.product', 'Products'),
        'product_uos_qty':fields.float('Quantity'),
        'uom_id':fields.many2one('product.uom', 'UOM', readonly=False),
#        'uom_id':fields.function(_get_uom_from_product, type='many2one', relation='product.uom', string='UOM'),
        'price_unit':fields.float('Unit Price'),
        'discount':fields.float('Discount (%)'),
        'discount_amt':fields.float('Discount (Amt)'),
        'order_id': fields.many2one('mobile.sale.order', 'Sale Order'),
        'sub_total':fields.float('Sub Total'),
        'foc':fields.boolean('FOC'),
    }
    _defaults = {
       'product_uos_qty':1.0,
    }   
    
mobile_sale_order_line()

class sale_group(osv.osv):
    _inherit = 'res.users' 
 
    
sale_group()

class mso_promotion_line(osv.osv):
    _name = 'mso.promotion.line'
    _columns = {
              'promo_line_id':fields.many2one('mobile.sale.order', 'Promotion line'),
              'pro_id': fields.many2one('promos.rules', 'Promotion Rule', change_default=True, readonly=False),
              'from_date':fields.datetime('From Date'),
              'to_date':fields.datetime('To Date')
              }
    
    def onchange_promo_id(self, cr, uid, ids, pro_id, context=None):
            result = {}
            promo_pool = self.pool.get('promos.rules')
            datas = promo_pool.read(cr, uid, pro_id, ['from_date', 'to_date'], context=context)
    
            if datas:
                result.update({'from_date':datas['from_date']})
                result.update({'to_date':datas['to_date']})
            return {'value':result}
            
mso_promotion_line()

class mobile_product_yet_to_deliver_line(osv.osv):
    
    _name = "products.to.deliver"
    _description = "Product Yet To Deliver"

    def _get_uom_from_product(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for rec in self.browse(cr, uid, ids, context=context):
            result[rec.id] = rec.product_id.uom_id
        return result       
                           
    _columns = {
        'product_id':fields.many2one('product.product', 'Products'),
        'uom':fields.function(_get_uom_from_product, type='many2one', relation='product.uom', string='UOM'),
        'product_qty':fields.float('Quantity'),
        'product_qty_to_deliver':fields.float('Quantity To Deliver'),
        'sale_order_id': fields.many2one('mobile.sale.order', 'Sale Order'),
                }
mobile_product_yet_to_deliver_line()

# class account_invoice(osv.osv):
  #  _inherit = "account.invoice"
  
    # _columns = {
         #    'payment_type': fields.char('Payment Type', size=64, readonly=True),
            #   }
# account_invoice()    
 
class sale_order(osv.osv):
    _inherit = "sale.order" 
    
    def _make_invoice(self, cr, uid, order, lines, context=None):
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        
        if context is None:
            context = {}
        invoiced_sale_line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', order.id), ('invoiced', '=', True)], context=context)
        from_line_invoice_ids = []
        for invoiced_sale_line_id in self.pool.get('sale.order.line').browse(cr, uid, invoiced_sale_line_ids, context=context):
            for invoice_line_id in invoiced_sale_line_id.invoice_lines:
                if invoice_line_id.invoice_id.id not in from_line_invoice_ids:
                    from_line_invoice_ids.append(invoice_line_id.invoice_id.id)
        for preinv in order.invoice_ids:
            if preinv.state not in ('cancel',) and preinv.id not in from_line_invoice_ids:
                for preline in preinv.invoice_line:
                    inv_line_id = obj_invoice_line.copy(cr, uid, preline.id, {'invoice_id': False, 'price_unit':-preline.price_unit})
                    lines.append(inv_line_id)
        inv = self._prepare_invoice(cr, uid, order, lines, context=context)
        # inv = self.prepare_invoice(cr, uid, order, lines, context=context)
        
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv['payment_term'], time.strftime(DEFAULT_SERVER_DATE_FORMAT))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        # self.message_post(cr, uid, [order.id], body=_("test created"), context=context)
        # inv_obj.message_post(cr, uid, [inv_id], body=_("test created"), context=context)
                
        
        if order.payment_type == 'credit':
            self.send_message_or_not(cr, uid, order.partner_invoice_id.credit_limit, order.amount_total, inv_id, context)
                
            # self.send_message_or_not(cr, uid, order.partner_invoice_id.credit_limit, order.amount_total, inv_id, order.id, context)
        return inv_id
    
    def send_message_or_not(self, cr, uid, credit_limit, total_amt, invoice_id, context=None):
        inv_obj = self.pool.get('account.invoice')
        
        if credit_limit < total_amt and credit_limit > 0:
            inv_obj.message_post(cr, uid, [invoice_id], body=_("Total amount exceed the credit limit"), context=context)  

        return True  
          
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).
    
           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        
        if context is None:
            context = {}
        journal_ids = self.pool['account.invoice'].default_get(cr, uid, ['journal_id'], context=context)['journal_id']
        if journal_ids:
            try:
                journal_ids = journal_ids[0]
            except Exception, e:
                journal_ids = journal_ids
                
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        payment_type = None
        if order.payment_type == 'credit':
            payment_type = 'Credit'    
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_invoice_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'journal_id': journal_ids,
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_invoice_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            'section_id' : order.section_id.id,
            'payment_type': payment_type,
        }
        
        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals           
sale_order()

class partner_photo(osv.osv):
    _name = "partner.photo"
    _description = "Patner Photo"

    _columns = {       
        'customer_id':fields.many2one('res.partner', 'Customer', domain="[('customer','=',True)]"),
        'customer_code':fields.char('Customer Code'),
        'comment':fields.char('comment'),
        'image_one':fields.binary('image_one'),
        'image_two':fields.binary('image_two'),
        'image_three':fields.binary('image_three'),
        'image_four':fields.binary('image_four'),
        'image_five':fields.binary('image_five')
       }
partner_photo()    