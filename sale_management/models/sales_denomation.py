from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from datetime import datetime
class sale_denomination(osv.osv):
    
    _name = "sales.denomination"
    _description = "Sales Denomination"         
    
    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        if not company_id:
            raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))
        return company_id        
    
    def _deno_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}        
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            for line in order.denomination_note_line:
                note_data=self.pool.get('sales.denomination.note.line').browse(cr, uid, line.id, context=context)
                note = note_data.notes
                note=note.replace(',','')
                qty = note_data.note_qty
                val1 += (float(note) * float(qty))                           
            res[order.id]= val1
        return res    
    
    def _invoice_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}                
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            for line in order.denomination_product_line:
                prouduct_data=self.pool.get('sales.denomination.product.line').browse(cr, uid, line.id, context=context)
                val1 += prouduct_data.amount                      
            res[order.id]= val1 
        return res

    def _cheque_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}                
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            for line in order.denomination_cheque_line:
                cheque_data=self.pool.get('sales.denomination.cheque.line').browse(cr, uid, line.id, context=context)
                val1 += cheque_data.amount                      
            res[order.id] = val1 
        return res    
    
    def _ar_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}               
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            for line in order.denomination_ar_line:
                ar_data=self.pool.get('sales.denomination.ar.line').browse(cr, uid, line.id, context=context)
                val1 += ar_data.amount                      
            res[order.id] = val1 # cur_obj.round(cr, uid, cur, val1)
        return res       

    def _bank_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}                
        for order in self.browse(cr, uid, ids, context=context):
            val1 = 0.0            
            for line in order.denomination_bank_line:
                bank_data=self.pool.get('sales.denomination.bank.line').browse(cr, uid, line.id, context=context)
                val1 += bank_data.amount                      
            res[order.id] = val1 # cur_obj.round(cr, uid, cur, val1)
        return res           
                
    def _dssr_ar_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}        
        ar_amount=self._ar_amount(cr, uid, ids, field_name, arg, context=context)
        product_amount=self._invoice_amount(cr, uid, ids, field_name, arg, context=context)
        val1=0.0
        for k, ar_amount in ar_amount.iteritems():
            ar_amount=ar_amount
        for k, product_amount in product_amount.iteritems():
            product_amount=product_amount
        for order in self.browse(cr, uid, ids, context=context):         
            discount_amount=order.discount_amount
            discount_total=order.discount_total
            val1=ar_amount+product_amount-discount_amount-discount_total
            res[order.id]=val1
        return res           
    
    def _trans_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}                
        deno_amount=self._deno_amount(cr, uid, ids, field_name, arg, context=context)
        cheque_amount=self._cheque_amount(cr, uid, ids, field_name, arg, context=context)
        bank_amount=self._bank_amount(cr, uid, ids, field_name, arg, context=context)
        for k, deno_amount in deno_amount.iteritems():
            deno_amount=deno_amount
        for k, cheque_amount in cheque_amount.iteritems():
            cheque_amount=cheque_amount
        for k, bank_amount in bank_amount.iteritems():
            bank_amount=bank_amount                  
        val1=0.0
        for order in self.browse(cr, uid, ids, context=context):             
            val1=deno_amount+cheque_amount+bank_amount
            res[order.id]= val1 

        return res      
    
    def _diff_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}                
        dssr_ar_amount=self._dssr_ar_amount(cr, uid, ids, field_name, arg, context=context)
        trans_amount=self._trans_amount(cr, uid, ids, field_name, arg, context=context)
        for k, dssr_ar_amount in dssr_ar_amount.iteritems():
            dssr_ar_amount=dssr_ar_amount
        for k, trans_amount in trans_amount.iteritems():
            trans_amount=trans_amount       
        val1=0.0
        for order in self.browse(cr, uid, ids, context=context):

            val1=dssr_ar_amount-trans_amount
            res[order.id]= val1 
        return res            
    
    _columns = {
        'company_id':fields.many2one('res.company', 'Company'),
        'date':fields.datetime('Date'),
        'sale_team_id':fields.many2one('crm.case.section', 'Sales Team' , required=True),
        'user_id':fields.many2one('res.users', 'Salesman Name'  , required=True, select=True, track_visibility='onchange'),
        'tablet_id':fields.char('Tablet ID'),
        'name':fields.char('Txn' , readonly=True),
        'invoice_count':fields.integer('Invoiced' , readonly=False),
       'denomination_product_line':fields.one2many('sales.denomination.product.line', 'denomination_product_ids', string='Sale denomination Product Line', copy=True),
       'denomination_note_line':fields.one2many('sales.denomination.note.line', 'denomination_note_ids', string='Sale denomination Product Line', copy=True),
       'denomination_cheque_line':fields.one2many('sales.denomination.cheque.line', 'denomination_cheque_ids', string='Sale denomination Cheque Line', copy=True),
       'denomination_ar_line':fields.one2many('sales.denomination.ar.line', 'denomination_ar_ids', string='Sale denomination AR Line', copy=True),
       'denomination_bank_line':fields.one2many('sales.denomination.bank.line', 'denomination_bank_ids', string='Sale denomination Bank Line', copy=True),
        'note':fields.text('Note'),
   #   'total_amount':fields.float('Denomination Total',digits_compute=dp.get_precision('Product Price')),
#       'product_amount':fields.float('Invoice Total', digits_compute=dp.get_precision('Product Price')),
#       'cheque_amount':fields.float('Cheque Total', digits_compute=dp.get_precision('Product Price')),
#       'ar_amount':fields.float('AR Total', digits_compute=dp.get_precision('Product Price')),
#       'bank_amount':fields.float('Bank Total', digits_compute=dp.get_precision('Product Price')),
#       'dssr_ar_amount':fields.float('Grand  Total', digits_compute=dp.get_precision('Product Price')),
#       'trans_amount':fields.float('Grand  Total', digits_compute=dp.get_precision('Product Price')),
#       'diff_amount':fields.float('Difference Amount', digits_compute=dp.get_precision('Product Price')),
      'partner_id':fields.many2one('res.partner', string='Partner'),
      'discount_amount':fields.float('Discount Amount', digits_compute=dp.get_precision('Product Price')),
      'discount_total':fields.float('Discount Total', digits_compute=dp.get_precision('Product Price')),
        'invoice_sub_total':fields.float('Sub Total',digits_compute=dp.get_precision('Product Price')),
          'total_amount':fields.function(_deno_amount, string='Denomination Total', digits_compute=dp.get_precision('Product Price'),type='float'),
     'product_amount':fields.function(_invoice_amount, string='Invoice Total', digits_compute=dp.get_precision('Product Price'),type='float'),
     'cheque_amount':fields.function(_cheque_amount, string='Cheque Total', digits_compute=dp.get_precision('Product Price'),type='float'),
     'ar_amount':fields.function(_ar_amount,string= 'AR Total', digits_compute=dp.get_precision('Product Price'),type='float'),
     'bank_amount':fields.function(_bank_amount, string='Bank Total', digits_compute=dp.get_precision('Product Price'),type='float'),
     'dssr_ar_amount':fields.function(_dssr_ar_amount,string= 'Grand  Total', digits_compute=dp.get_precision('Product Price'),type='float'),
     'trans_amount':fields.function(_trans_amount, string='Grand  Total', digits_compute=dp.get_precision('Product Price'),type='float'),
     'diff_amount':fields.function(_diff_amount,string= 'Difference Amount', digits_compute=dp.get_precision('Product Price'),type='float'),
    'invoice_sub_total':fields.function(_invoice_amount,string= 'Sub Total', digits_compute=dp.get_precision('Product Price'),type='float'),
         }
    _defaults = {
        'date': fields.datetime.now,
        'company_id': _get_default_company,
        }   
    
    def on_change_date(self, cr, uid, ids, date, user_id, context=None):
        value = {}
        note = [{'notes':10000, 'note_qty':False}, {'notes':5000, 'note_qty':False}, {'notes':1000, 'note_qty':False}, {'notes':500, 'note_qty':False}, {'notes':100, 'note_qty':False}, {'notes':50, 'note_qty':False}, {'notes':10, 'note_qty':False}, {'notes':1, 'note_qty':False}]
        order_line_data = []
        cheque_data = []
        ar_data = []
        transfer_data = []
        team_id = None
        payment_ids = None
        ar_payment_ids = None
        tablet_id = None
        bank_ids = None
        ar_bank_ids = None        
        invoice_count = None
        discount_amount = 0.0
        discount_total = 0.0
        product_amount = 0.0
        if date:
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            de_date = date.date()
            mobile_sale_obj = self.pool.get('mobile.sale.order')        
            invoice_obj = self.pool.get('account.invoice')
            invoice_line_obj = self.pool.get('account.invoice.line')
            payment_obj = self.pool.get('customer.payment')
            ar_obj = self.pool.get('ar.payment')
            if user_id:
                cr.execute("select default_section_id from res_users where id= %s ", (user_id,))
                team_id = cr.fetchone()[0]            
            mobile_ids = invoice_obj.search(cr, uid, [('date_invoice', '=', de_date), ('state', '=', 'open'), ('user_id', '=', user_id)], context=context)
            if team_id:
                cr.execute("select id from customer_payment where date=%s and sale_team_id=%s and payment_code='CHEQ' ", (de_date, team_id,))
                payment_ids = cr.fetchall()
            if team_id:
                cr.execute("select name from tablets_information where sale_team_id=%s", (team_id,))
                tablet_id = cr.fetchone()[0]
                cr.execute("select id from ar_payment where date=%s and sale_team_id=%s and payment_code='CHEQ' ", (de_date, team_id,))
                ar_payment_ids = cr.fetchall()
            if team_id:
                cr.execute("select id from customer_payment where date=%s and sale_team_id=%s and payment_code='BNK' ", (de_date, team_id,))
                bank_ids = cr.fetchall()
            if team_id:
                cr.execute("select id from ar_payment where date=%s and sale_team_id=%s and payment_code='BNK' ", (de_date, team_id,))
                ar_bank_ids = cr.fetchall()                
                
            if  user_id:
                cr.execute("""select m.date,a.id,m.partner_id,m.payment_amount
                                from account_invoice as a,mobile_ar_collection as m
                                where m.ref_no = a.number and  m.state='draft'  and
                                m.user_id=%s and m.sale_team_id=%s and m.date = %s  
                    """, (user_id, team_id, de_date,))
                vals = cr.fetchall()             
                for val in vals:
                    data_id = {'invoice_id':val[1],
                                'date':val[0],
                                'partner_id':val[2],
                                'amount':val[3],
                                'payment_type':'Credit'}
                    ar_data.append(data_id)
            if  mobile_ids:
                pre_mobile_ids = []
                discount_amount = 0.0
                product_amount = 0.0
                discount_total = 0.0
                cr.execute("select id from account_invoice where date_invoice=%s and section_id =%s and state='open' ", (de_date, team_id,))
                mobile_ids = cr.fetchall()       
                for data_pro in mobile_ids:
                    pre_mobile_ids.append(data_pro[0])
                if  pre_mobile_ids:
                    line_ids = invoice_line_obj.search(cr, uid, [('invoice_id', 'in', tuple(pre_mobile_ids))], context=context)   
                    order_line_ids = invoice_line_obj.browse(cr, uid, line_ids, context=context)                
                    cr.execute('select product_id,sum(quantity) as quantity,sum(price_subtotal) as  sub_total from account_invoice_line where id in %s group by product_id', (tuple(order_line_ids.ids),))
                    order_line = cr.fetchall()
                    for data in order_line:
                        product = self.pool.get('product.product').browse(cr, uid, data[0], context=context)
                        sequence = product.sequence
                        product_amount += data[2]
                        data_id = {'product_id':data[0],
                                          'product_uom_qty':data[1],
                                          'sequence':sequence,
                                          'amount':data[2]}
                        order_line_data.append(data_id)
                    mobile_data = invoice_obj.search(cr, uid, [('id', 'in', tuple(pre_mobile_ids))], context=context)   
                    invoice_count = len(mobile_data)
                    for mobile_id  in mobile_data:
                        cr.execute('select deduct_amt,amount_untaxed,additional_discount from account_invoice where id =%s', (mobile_id,))
                        invoice_data = cr.fetchone()          
                        deduct_amt = invoice_data[0]
                        amount_total = invoice_data[1]
                        deduct_percent = invoice_data[2] / 100
                        discount_total += amount_total * deduct_percent
                        discount_amount += deduct_amt
            if  payment_ids:
                for payment in payment_ids:
                    payment_data = payment_obj.browse(cr, uid, payment, context=context)                  
                    partner_id = payment_data.partner_id.id
                    journal_id = payment_data.journal_id.id
                    cheque_no = payment_data.cheque_no
                    amount = payment_data.amount
                    data_id = {'partner_id':partner_id,
                                      'journal_id':journal_id,
                                      'cheque_no':cheque_no,
                                      'amount': amount, }
                    cheque_data.append(data_id)                    
            if  ar_payment_ids:
                for payment in ar_payment_ids:
                    payment_data = ar_obj.browse(cr, uid, payment, context=context)                  
                    partner_id = payment_data.partner_id.id
                    journal_id = payment_data.journal_id.id
                    cheque_no = payment_data.cheque_no
                    amount = payment_data.amount
                    data_id = {'partner_id':partner_id,
                                      'journal_id':journal_id,
                                      'cheque_no':cheque_no,
                                      'amount': amount, }
                    cheque_data.append(data_id)                   
            if  bank_ids:
                for bank in bank_ids:
                    bank_data = payment_obj.browse(cr, uid, bank, context=context)                  
                    partner_id = bank_data.partner_id.id
                    journal_id = bank_data.journal_id.id
                    amount = bank_data.amount
                    data_id = {'partner_id':partner_id,
                                      'journal_id':journal_id,
                                      'amount': amount, }
                    transfer_data.append(data_id)              
            if  ar_bank_ids:
                for bank in ar_bank_ids:
                    bank_data = ar_obj.browse(cr, uid, bank, context=context)                  
                    partner_id = bank_data.partner_id.id
                    journal_id = bank_data.journal_id.id
                    amount = bank_data.amount
                    data_id = {'partner_id':partner_id,
                                      'journal_id':journal_id,
                                      'amount': amount, }
                    transfer_data.append(data_id)                    
            value['value'] = {           'tablet_id':tablet_id,
                                             'invoice_count':invoice_count,
                                            'denomination_product_line': order_line_data ,
                                            'denomination_note_line':note,
                                            'denomination_cheque_line':cheque_data,
                                            'denomination_ar_line':ar_data,
                                            'denomination_bank_line':transfer_data,
                                            'discount_amount':discount_amount,
                                            'discount_total':discount_total,
                                            'invoice_sub_total':product_amount - discount_amount - discount_total,
                                            } 
                
        return value      

    def create(self, cursor, user, vals, context=None):
        credit_no = self.pool.get('ir.sequence').get(cursor, user,
            'sales.denomination') or '/'
        vals['name'] = credit_no
        return super(sale_denomination, self).create(cursor, user, vals, context=context)
    
#     def write(self, cursor, user, ids, vals, context=None):
#         data=self.browse(cursor, user,ids, context=context)           
#         total_amount = 0
#         deno_amount = 0
#         cheque_amount = 0
#         bank_amount = 0
#         ar_amount = 0
#         note_obj=self.pool.get('sales.denomination.note.line')
#         product_obj=self.pool.get('sales.denomination.product.line')
#         cheque_obj=self.pool.get('sales.denomination.cheque.line')
#         bank_obj=self.pool.get('sales.denomination.bank.line')
#         ar_obj=self.pool.get('sales.denomination.ar.line')
#         denomination_note_line = data.denomination_note_line
#         denomination_product_line = data.denomination_product_line
#         denomination_cheque_line = data.denomination_cheque_line
#         denomination_bank_line = data.denomination_bank_line
#         denomination_ar_line = data.denomination_ar_line
#         if denomination_product_line:
#             for p_data in denomination_product_line:
#                 product=product_obj.browse(cursor, user,p_data.id, context=context)           
#                 print 'product',product
#                 amount = product.amount
#                 deno_amount += amount
#         discount_amount=data.discount_amount
#         discount_total=data.discount_total
#         product_amount= deno_amount -discount_amount-discount_total
#         if denomination_note_line:
#             for data in denomination_note_line:
#                 note_data=note_obj.browse(cursor, user,data.id, context=context)           
#                 note = note_data.notes
#                 note=note.replace(',', '')
#                 qty = note_data.note_qty
#                 total_amount += (int(note) * int(qty))
#         if denomination_cheque_line:
#             for data in denomination_cheque_line:
#                 cheque=cheque_obj.browse(cursor, user,data.id, context=context)           
#                 amount = cheque.amount
#                 cheque_amount += amount
#         if denomination_bank_line:
#             for data in denomination_bank_line:
#                 bank=bank_obj.browse(cursor, user,data.id, context=context)           
#                 amount = bank.amount
#                 bank_amount += amount
#         if denomination_ar_line:
#             for data in denomination_ar_line:
#                 ar_data=ar_obj.browse(cursor, user,data.id, context=context)           
#                 amount = ar_data.amount
#                 ar_amount += amount
#         vals['product_amount'] = product_amount
#         vals['total_amount']= total_amount
#         vals['cheque_amount'] = cheque_amount
#         vals['bank_amount'] = bank_amount
#         vals['ar_amount'] = ar_amount
#         vals['trans_amount'] = total_amount + cheque_amount + bank_amount
#         vals['dssr_ar_amount']=ar_amount+deno_amount -discount_amount-discount_total
#         vals['invoice_sub_total']=deno_amount -discount_amount -discount_total
#         vals['diff_amount'] = (ar_amount+deno_amount-discount_amount-discount_total)-( total_amount + cheque_amount + bank_amount)                
#         print 'valsssssssss',vals
#         return super(sale_denomination, self).write(cursor, user, ids, vals, context=context)
    
    def button_dummy(self, cursor, user, ids, context=None):
        return True
                
#         total_amount = 0
#         deno_amount = 0
#         cheque_amount = 0
#         bank_amount = 0
#         ar_amount = 0
#         note_obj=self.pool.get('sales.denomination.note.line')
#         product_obj=self.pool.get('sales.denomination.product.line')
#         cheque_obj=self.pool.get('sales.denomination.cheque.line')
#         bank_obj=self.pool.get('sales.denomination.bank.line')
#         ar_obj=self.pool.get('sales.denomination.ar.line')
#         denomination_note_line = data.denomination_note_line
#         denomination_product_line = data.denomination_product_line
#         denomination_cheque_line = data.denomination_cheque_line
#         denomination_bank_line = data.denomination_bank_line
#         denomination_ar_line = data.denomination_ar_line
#         if denomination_product_line:
#             for p_data in denomination_product_line:
#                 product=product_obj.browse(cursor, user,p_data.id, context=context)           
#                 print 'product',product
#                 amount = product.amount
#                 deno_amount += amount
#         discount_amount=data.discount_amount
#         discount_total=data.discount_total
#         product_amount= deno_amount -discount_amount-discount_total
#         if denomination_note_line:
#             for data in denomination_note_line:
#                 note_data=note_obj.browse(cursor, user,data.id, context=context)           
#                 note = note_data.notes
#                 note=note.replace(',', '')
#                 qty = note_data.note_qty
#                 total_amount += (int(note) * int(qty))
#         if denomination_cheque_line:
#             for data in denomination_cheque_line:
#                 cheque=cheque_obj.browse(cursor, user,data.id, context=context)           
#                 amount = cheque.amount
#                 cheque_amount += amount
#         if denomination_bank_line:
#             for data in denomination_bank_line:
#                 bank=bank_obj.browse(cursor, user,data.id, context=context)           
#                 amount = bank.amount
#                 bank_amount += amount
#         if denomination_ar_line:
#             for data in denomination_ar_line:
#                 ar_data=ar_obj.browse(cursor, user,data.id, context=context)           
#                 amount = ar_data.amount
#                 ar_amount += amount
#         total_amount= total_amount
#         cheque_amount= cheque_amount
#         bank_amount= bank_amount
#         ar_amount= ar_amount
#         trans_amount= total_amount + cheque_amount + bank_amount
#         dssr_ar_amount=ar_amount+deno_amount -discount_amount-discount_total
#         invoice_sub_total=deno_amount -discount_amount -discount_total
#         diff_amount = (ar_amount+deno_amount-discount_amount-discount_total)-( total_amount + cheque_amount + bank_amount)
#         cursor.execute("update sales_denomination set product_amount=%s,total_amount=%s,cheque_amount=%s,bank_amount=%s,ar_amount=%s,trans_amount=%s,dssr_ar_amount=%s,invoice_sub_total=%s,diff_amount=%s where id= %s",(product_amount,total_amount,cheque_amount,bank_amount,ar_amount,trans_amount,dssr_ar_amount,invoice_sub_total,diff_amount,data.id,))
#         return True
sale_denomination()               

class sale_denomination_product_line(osv.osv):    
    _name = 'sales.denomination.product.line'
    _columns = {
                'denomination_product_ids': fields.many2one('sales.denomination', 'Sales denomination'),
                'product_id':fields.many2one('product.product', 'Product', required=False),
                'product_uom_qty':fields.integer('QTY', required=False),
                'amount':fields.float('Amount', required=False, digits_compute=dp.get_precision('Product Price')),
                'sequence':fields.integer('Sequence'),
                }
sale_denomination_product_line()    

class sale_denomination_note_line(osv.osv):    
    _name = 'sales.denomination.note.line'
    
    def on_change_note_qty(self, cr, uid, ids, notes, note_qty, context=None):
        values = {}
        if notes and note_qty:
            notes = notes.replace(',', '')
            values = {
                'amount':float(notes) * note_qty,
            }
        return {'value': values}   
    
    _columns = {
                'denomination_note_ids': fields.many2one('sales.denomination', 'Sales Denomination'),
                'notes':fields.char('Notes', required=True),
                'note_qty':fields.integer('Qty', required=True),
                'amount':fields.float('Total', digits_compute=dp.get_precision('Product Price')),
                }
    _defaults = {
        'amount': 0.0,
        }   
sale_denomination_note_line()    

class sale_denomination_cheque_line(osv.osv):    
    _name = 'sales.denomination.cheque.line'
    
    _columns = {
                'denomination_cheque_ids': fields.many2one('sales.denomination', 'Sales Denomination'),
                'cheque_no':fields.char('Cheque No', required=True),
                'partner_id':fields.many2one('res.partner', 'Customer', required=True),
                'amount':fields.float('Total', digits_compute=dp.get_precision('Product Price')),
                'journal_id':fields.many2one('account.journal', "Journal"),
                }
    _defaults = {
        'amount': 0.0,
        }   
    
sale_denomination_cheque_line()    
class sale_denomination_ar_line(osv.osv):    
    _name = 'sales.denomination.ar.line'
    
    _columns = {
                'denomination_ar_ids': fields.many2one('sales.denomination', 'Sales Denomination'),
                'invoice_id':fields.many2one('account.invoice', 'Invoice No', ondelete='cascade'),
                'date':fields.date('Date'),
                'selected':fields.boolean('Selected' , default=True),
                'partner_id':fields.many2one('res.partner', 'Customer', ondelete='cascade'),
                'payment_type': fields.text('Type'),
                'amount':fields.float('Amount' , digits_compute=dp.get_precision('Product Price')),
                }
    _defaults = {
        'amount': 0.0,
        }   
    
sale_denomination_ar_line()    

class sale_denomination_bank_line(osv.osv):    
    _name = 'sales.denomination.bank.line'
    
    _columns = {
                'denomination_bank_ids': fields.many2one('sales.denomination', 'Sales Denomination'),
                'partner_id':fields.many2one('res.partner', 'Customer', required=True),
                'amount':fields.float('Total', digits_compute=dp.get_precision('Product Price')),
                'journal_id':fields.many2one('account.journal', "Journal"),
                }
    _defaults = {
        'amount': 0.0,
        }   
    
sale_denomination_bank_line()    
