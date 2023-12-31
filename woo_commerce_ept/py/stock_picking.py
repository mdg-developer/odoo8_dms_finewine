from openerp import models,fields,api,_
class stock_picking(models.Model):
    _inherit="stock.picking"
    
    @api.one
    @api.depends("group_id")
    def get_woo_orders(self):
        sale_obj=self.env['sale.order']
        for record in self:
            if record.group_id:
                sale_order=sale_obj.search([('procurement_group_id', '=', record.group_id.id)])
                if sale_order.woo_order_id:
                    record.is_woo_delivery_order=True
                    record.woo_instance_id=sale_order.woo_instance_id.id
                else:
                    record.is_woo_delivery_order=False
                    record.woo_instance_id=False
    updated_in_woo=fields.Boolean("Updated In Woo Commerce",default=False)
    is_woo_delivery_order=fields.Boolean("Woo Commerce Delivery Order",compute="get_woo_orders",store=True)
    woo_instance_id=fields.Many2one("woo.instance.ept","Instance",store=True,compute="get_woo_orders")
    pack_operation_ids=fields.One2many('stock.pack.operation', 'picking_id', string='Related Packing Operations',states={'cancel': [('readonly', True)]})
    canceled_in_woo=fields.Boolean("Canceled In woo",default=False)
    

    @api.multi
    def cancel_in_woo(self):
        view=self.env.ref('woo_commerce_ept.view_woo_cancel_order_wizard')
        return {
            'name': _('Cancel Order In woo'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'woo.cancel.order.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self._context
        }        
    
    @api.multi
    def mark_sent_woo(self):
        for picking in self:
            picking.write({'updated_in_woo':False})
        return True
    @api.multi
    def mark_not_sent_woo(self):
        for picking in self:
            picking.write({'updated_in_woo':True})
        return True
    
class delivery_carrier(models.Model):
    _inherit="delivery.carrier"
    
    woo_code=fields.Char("woo Code")
    