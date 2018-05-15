from datetime import date, datetime
import time
from openerp.osv import fields, osv
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import SUPERUSER_ID, api

class stock_inventory(osv.osv):
    _inherit = 'stock.inventory'   
    _columns = {
        'name': fields.char('Inventory Reference', required=False, readonly=True, help="Inventory Name."),

              }
    
    def prepare_inventory(self, cr, uid, ids, context=None):
        inventory_line_obj = self.pool.get('stock.inventory.line')
        
        for inventory in self.browse(cr, uid, ids, context=context):
            # If there are inventory lines already (e.g. from import), respect those and set their theoretical qty
            line_ids = [line.id for line in inventory.line_ids]
            if not line_ids and inventory.filter != 'partial':
                #compute the inventory lines and create them
                vals = self._get_inventory_lines(cr, uid, inventory, context=context)
                for product_line in vals:
                    inventory_line_obj.create(cr, uid, product_line, context=context)
        id_code = self.pool.get('ir.sequence').get(cr, uid,
                                                'stock.inventory') or '/'
        return self.write(cr, uid, ids, {'name':id_code,'state': 'confirm', 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
    
    

    def post_inventory(self, cr, uid, inv, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        if inv.period_id:
            ctx['force_period'] = inv.period_id.id
        #add ref auto name in account move
        if inv.name:
            ctx['ref'] = inv.name           
        return super(stock_inventory, self).post_inventory(cr, uid, inv, context=ctx)    
    
class stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line"    
    _columns = {
        'note': fields.text('Remark', required=False),

              }    
    def _resolve_inventory_line(self, cr, uid, inventory_line, context=None):
        stock_move_obj = self.pool.get('stock.move')
        quant_obj = self.pool.get('stock.quant')
        diff = inventory_line.theoretical_qty - inventory_line.product_qty
        if not diff:
            return
        #each theorical_lines where difference between theoretical and checked quantities is not 0 is a line for which we need to create a stock move
        vals = {
            #'name': _('INV:') + (inventory_line.inventory_id.name or ''),
            'name':inventory_line.product_id.name_template,
            'product_id': inventory_line.product_id.id,
            'product_uom': inventory_line.product_uom_id.id,
            'date': inventory_line.inventory_id.date,
            'company_id': inventory_line.inventory_id.company_id.id,
            'inventory_id': inventory_line.inventory_id.id,
            'state': 'confirmed',
            'restrict_lot_id': inventory_line.prod_lot_id.id,
            'restrict_partner_id': inventory_line.partner_id.id,
         }
        inventory_location_id = inventory_line.product_id.property_stock_inventory.id
        if diff < 0:
            #found more than expected
            vals['location_id'] = inventory_location_id
            vals['location_dest_id'] = inventory_line.location_id.id
            vals['product_uom_qty'] = -diff
        else:
            #found less than expected
            vals['location_id'] = inventory_line.location_id.id
            vals['location_dest_id'] = inventory_location_id
            vals['product_uom_qty'] = diff
        move_id = stock_move_obj.create(cr, uid, vals, context=context)
        move = stock_move_obj.browse(cr, uid, move_id, context=context)
        if diff > 0:
            domain = [('qty', '>', 0.0), ('package_id', '=', inventory_line.package_id.id), ('lot_id', '=', inventory_line.prod_lot_id.id), ('location_id', '=', inventory_line.location_id.id)]
            preferred_domain_list = [[('reservation_id', '=', False)], [('reservation_id.inventory_id', '!=', inventory_line.inventory_id.id)]]
            quants = quant_obj.quants_get_prefered_domain(cr, uid, move.location_id, move.product_id, move.product_qty, domain=domain, prefered_domain_list=preferred_domain_list, restrict_partner_id=move.restrict_partner_id.id, context=context)
            quant_obj.quants_reserve(cr, uid, quants, move, context=context)
        elif inventory_line.package_id:
            stock_move_obj.action_done(cr, uid, move_id, context=context)
            quants = [x.id for x in move.quant_ids]
            quant_obj.write(cr, SUPERUSER_ID, quants, {'package_id': inventory_line.package_id.id}, context=context)
            res = quant_obj.search(cr, uid, [('qty', '<', 0.0), ('product_id', '=', move.product_id.id),
                                    ('location_id', '=', move.location_dest_id.id), ('package_id', '!=', False)], limit=1, context=context)
            if res:
                for quant in move.quant_ids:
                    if quant.location_id.id == move.location_dest_id.id: #To avoid we take a quant that was reconcile already
                        quant_obj._quant_reconcile_negative(cr, uid, quant, move, context=context)
        return move_id    
    
class stock_quant(osv.osv):
    _inherit = "stock.quant"        
    
    def _create_account_move_line(self, cr, uid, quants, move, credit_account_id, debit_account_id, journal_id, context=None):
        #group quants by cost
        quant_cost_qty = {}
        for quant in quants:
            if quant_cost_qty.get(quant.cost):
                quant_cost_qty[quant.cost] += quant.qty
            else:
                quant_cost_qty[quant.cost] = quant.qty
        move_obj = self.pool.get('account.move')
        for cost, qty in quant_cost_qty.items():
            move_lines = self._prepare_account_move_line(cr, uid, move, qty, cost, credit_account_id, debit_account_id, context=context)
            period_id = context.get('force_period', self.pool.get('account.period').find(cr, uid, context=context)[0])
            ref_no=context.get('ref')
            if ref_no:
                move_obj.create(cr, uid, {'journal_id': journal_id,
                                      'line_id': move_lines,
                                      'period_id': period_id,
                                      'date': fields.date.context_today(self, cr, uid, context=context),
                                      'ref': ref_no}, context=context)
            else:
                
                move_obj.create(cr, uid, {'journal_id': journal_id,
                                          'line_id': move_lines,
                                          'period_id': period_id,
                                          'date': fields.date.context_today(self, cr, uid, context=context),
                                          'ref': move.picking_id.name}, context=context)
class account_move_line(osv.osv):
    _inherit = "account.move.line"    
    _columns = {
        'note': fields.text('Remark', required=False),

              }    