from openerp.osv import orm
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.osv.fields import _column
import xmlrpclib
import logging
from openerp.tools.translate import _

class stock_picking(osv.osv):
    _inherit = "stock.picking"

    _columns = {

        'is_sync_odoo16': fields.boolean('Is Sync Odoo'),
    }
    _defaults = {
        'is_sync_odoo16': False,
    }

    def sync_to_odoo(self, cr, uid, ids, context=None):
        sd_uid, url, db, password = self.pool['odoo16.connection'].get_connection_data(cr, uid, context=None)
        models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
        move_ids = []
        picking_id = False
        # warehouse_id = models.execute_kw(db, sd_uid, password,
        #                                  'stock.warehouse', 'search',
        #                                  [[['name', 'like', 'SG Main WH'], ['company_id', '=', 3]]],
        #                                  {'limit': 1})
        warehouse_id = [1]
        dest_loc_id = 34710

        loc_id = models.execute_kw(db, sd_uid, password,
                                   'stock.location', 'search',
                                   [[['usage', '=', 'customer']]],
                                   {'limit': 1})
        try:
            if warehouse_id:


                for picking in self.browse(cr, uid, ids[0], context=context)[0]:
                    reverse_name = str(picking.name)
                    picking_vals = {}
                    picking_vals['move_ids'] = []
                    resyc_picking = models.execute_kw(db, sd_uid, password,
                                                      'stock.picking', 'search',
                                                      [[['origin', '=', reverse_name],
                                                        ['state', '=', 'done']]],
                                                      {'limit': 1})
                    logging.warning("resyc_picking search>>>> sss15: %s", resyc_picking)
                    if not resyc_picking or len(resyc_picking) == 0:
                        if (picking.location_id.is_cellar_location == True and picking.picking_type_id.name == 'Internal Transfers') or ( picking.location_dest_id.is_cellar_location == True and picking.picking_type_id.name == 'Internal Transfers'):

                            logging.warning("picking location>>>> sss15: %s", picking.location_id.is_cellar_location)
                            if picking.location_id.is_cellar_location == True:


                                loc_id = [8]
                                dest_loc_id = 17
                                picking_type_id = [2]

                            elif picking.location_dest_id.is_cellar_location == True:


                                loc_id = [17]
                                dest_loc_id = 8
                                picking_type_id = [1]

                            logging.warning("picking picking_type_id>>>> sss15: %s", picking_type_id[0])
                            res = {
                                'partner_id': False,
                                'picking_type_id': picking_type_id[0],
                                'location_id': dest_loc_id,
                                'location_dest_id': loc_id[0],
                                'origin': reverse_name,
                                'company_id': 1,
                                'date_done': picking.date_done or picking.min_date,
                                'scheduled_date': picking.min_date,
                                'state': 'draft',
                            }
                            picking_vals['picking_type_id'] = picking_type_id[0]
                            picking_vals['location_id'] = loc_id[0]
                            picking_vals['location_dest_id'] = dest_loc_id
                            picking_vals['origin'] = reverse_name
                            picking_vals['state'] = 'draft'
                            picking_vals['scheduled_date'] = picking.min_date
                            picking_vals['date_done'] = picking.date_done or picking.min_date

                            # picking_id = models.execute_kw(db, sd_uid, password, 'stock.picking', 'create', [res])
                            # logging.warning("picking create id>>>> sss15: %s", picking_id[0])
                            for line in picking.move_lines:
                                product_id = False
                                if not warehouse_id and loc_id and dest_loc_id and picking_type_id:
                                    raise orm.except_orm(_('Error :'), _("Warehouse and Location doesn't exit in SD"))
                                if line.product_id.type != 'service':
                                    total_qty = line.product_uom_qty
                                    if line.product_uom.uom_type == 'bigger':
                                        total_qty = line.product_uom_qty * (1 / line.product_uom.factor)
                                        total_qty = round(total_qty, 4)
                                    # if line.product_id.product_tmpl_id.odoo16_pp_id != 0 or line.product_id.product_tmpl_id.odoo16_pp_id:
                                    #     product_id = line.product_id.product_tmpl_id.odoo16_pp_id
                                    # else:
                                    product_id = models.execute_kw(db, sd_uid, password,
                                                                   'product.product', 'search',
                                                                   [[['default_code', '=', line.product_id.default_code]]],
                                                                   {'limit': 1})
                                    if not product_id or len(product_id) == 0:
                                        logging.warning("product_id not fount>>>> sss15: %s", line.product_id.name)
                                        raise osv.except_osv(_('Error!'), _('product code %s doesn\'t exist in Cellar18!') % (line.product_id.default_code,))

                                    logging.warning("picking product_id search>>>> sss15: %s", product_id[0])
                                    if product_id:
                                        move_val = {

                                            'product_id': product_id[0],
                                            'product_uom_qty': total_qty,  # line.product_qty,
                                            # 'qty_done': line.product_uom_qty,
                                            'location_id': loc_id[0],
                                            'location_dest_id': dest_loc_id,
                                            # 'product_qty':line.product_uom_qty,
                                            'product_uom': 1,  # line.product_uom.id,
                                            'name': line.name,
                                            'picking_id': picking_id,
                                            'company_id': 1,
                                            'date': picking.min_date,
                                            'date_deadline': picking.date_done or picking.min_date,
                                        }
                                        picking_vals['move_ids'].append(
                                            [0, False,
                                             {'product_id': product_id[0], 'product_uom_qty': total_qty,
                                              'location_id': loc_id[0], 'quantity_done': total_qty,
                                              'name': line.name, 'date': picking.min_date,
                                              'date_deadline': picking.date_done or picking.min_date,
                                              'location_dest_id': dest_loc_id, 'product_uom': 1}])
                                        # move_id = models.execute_kw(db, sd_uid, password, 'stock.move', 'create', [move_val])

                                        # move_ids.append(move_id)
                            logging.warning("picking create value list>>>> sss15: %s", picking_vals)
                            picking_id = models.execute_kw(db, sd_uid, password, 'stock.picking', 'create', [picking_vals])
                            logging.warning("picking create picking id>>>> sss15: %s", picking_id)
                            models.execute_kw(db, sd_uid, password, 'stock.picking', 'action_confirm', [picking_id])
                            # models.execute_kw(db, sd_uid, password, 'stock.picking', 'action_set_quantities_to_reservation', [picking_id])

                            models.execute_kw(db, sd_uid, password, 'stock.picking', 'button_validate', [picking_id])
                            # models.execute_kw(db, sd_uid, password, 'stock.picking', 'action_done_custom', [picking_id])
                            models.execute_kw(db, sd_uid, password, 'stock.picking', 'write',
                                              [[picking_id], {'date_done': picking.date_done or picking.min_date,
                                                              'scheduled_date': picking.min_date,
                                                              'date_deadline': picking.min_date}])
                            self.write(cr, uid, picking.id, {'is_sync_odoo16': True}, context=context)

        except Exception as error:
            logging.warning("picking create value post error>>>> sss15: %s", error)
            if picking_id:
                try:
                    models.execute_kw(db, sd_uid, password, 'stock.picking', 'unlink', [picking_id])
                except Exception, e:
                    logging.warning("picking cancel unlink >>>> sss15: %s", e)
                    raise osv.except_osv(_('Error!'), _(error))
            raise osv.except_osv(_('Error!'),_(error))


        return True


    def do_enter_transfer_details(self, cr, uid, picking, context=None):
        logging.warning("do_enter_transfer_details >>>> sss15: %s", picking)
        result = super(stock_picking, self).do_enter_transfer_details(cr, uid, picking, context)
        sd_uid, url, db, password = self.pool['odoo16.connection'].get_connection_data(cr, uid, context=None)
        models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
        move_ids = []
        picking_id = False
        # warehouse_id = models.execute_kw(db, sd_uid, password,
        #                                  'stock.warehouse', 'search',
        #                                  [[['name', 'like', 'SG Main WH'], ['company_id', '=', 3]]],
        #                                  {'limit': 1})
        warehouse_id =[1]
        dest_loc_id = 34710

        #loc_id = models.execute_kw(db, sd_uid, password,
        #                           'stock.location', 'search',
        #                           [[['usage', '=', 'customer']]],
        #                           {'limit': 1})
        try:
            if warehouse_id:


                for picking in self.browse(cr, uid, picking[0], context=context)[0]:
                    reverse_name = str(picking.name)
                    picking_vals = {}
                    picking_vals['move_ids'] = []
                    if (picking.location_id.is_cellar_location == True and picking.picking_type_id.name == 'Internal Transfers') or (picking.location_dest_id.is_cellar_location == True and picking.picking_type_id.name == 'Internal Transfers'):
                        logging.warning("picking location>>>> sss15: %s", picking.location_id.is_cellar_location)
                        if picking.location_id.is_cellar_location == True:

                            # loc_id = models.execute_kw(db, sd_uid, password,
                            #                            'stock.location', 'search',
                            #                            [[['usage', '=', 'customer']]],
                            #                            {'limit': 1})
                            loc_id = [8]
                            dest_loc_id = 17
                            picking_type_id = [2]
                            # models.execute_kw(db, sd_uid, password,
                            #                                     'stock.picking.type', 'search',
                            #                                     [[['warehouse_id', '=', warehouse_id[0]],
                            #                                       ['code', '=', 'outgoing']
                            #                                       ]],
                            #                                     {'limit': 1})
                        elif picking.location_dest_id.is_cellar_location == True:

                            # loc_id = models.execute_kw(db, sd_uid, password,
                            #                            'stock.location', 'search',
                            #                            [[['usage', '=', 'customer']]],
                            #                            {'limit': 1})
                            loc_id = [17]
                            dest_loc_id = 8
                            picking_type_id =[1]
                            # models.execute_kw(db, sd_uid, password,
                            #                                     'stock.picking.type', 'search',
                            #                                     [[['warehouse_id', '=', warehouse_id[0]],
                            #                                       ['code', '=', 'incoming']
                            #                                       ]],
                            #                                     {'limit': 1})
                        logging.warning("picking picking_type_id>>>> sss15: %s", picking_type_id[0])
                        res = {
                            'partner_id': False,
                            'picking_type_id': picking_type_id[0],
                            'location_id': dest_loc_id,
                            'location_dest_id': loc_id[0],
                            'origin': reverse_name,
                            'company_id': 1,
                            'date_done':picking.date_done or picking.min_date,
                            'scheduled_date':picking.min_date,
                            'state': 'draft',
                        }
                        picking_vals['picking_type_id'] = picking_type_id[0]
                        picking_vals['location_id'] = loc_id[0]
                        picking_vals['location_dest_id'] = dest_loc_id
                        picking_vals['origin'] = reverse_name
                        picking_vals['state'] = 'draft'
                        picking_vals['scheduled_date'] = picking.min_date
                        picking_vals['date_done'] = picking.date_done or picking.min_date

                        #picking_id = models.execute_kw(db, sd_uid, password, 'stock.picking', 'create', [res])
                        #logging.warning("picking create id>>>> sss15: %s", picking_id[0])
                        for line in picking.move_lines:
                            product_id = False
                            if not warehouse_id and loc_id and dest_loc_id and picking_type_id:
                                raise orm.except_orm(_('Error :'), _("Warehouse and Location doesn't exit in SD"))
                            if line.product_id.type != 'service':
                                total_qty = line.product_uom_qty
                                if line.product_uom.uom_type == 'bigger':
                                    total_qty = line.product_uom_qty * (1/line.product_uom.factor)
                                    total_qty = round(total_qty,4)
                                # if line.product_id.product_tmpl_id.odoo16_pp_id != 0 or line.product_id.product_tmpl_id.odoo16_pp_id:
                                #     product_id = line.product_id.product_tmpl_id.odoo16_pp_id
                                # else:
                                product_id = models.execute_kw(db, sd_uid, password,
                                                                    'product.product', 'search',
                                                                    [[['default_code', '=', line.product_id.default_code]]],
                                                                    {'limit': 1})
                                if not product_id or len(product_id) == 0:
                                    raise osv.except_osv(_('Error!'), _('product code %s doesn\'t exist in Cellar18!') % (
                                    line.product_id.default_code,))
                                logging.warning("picking product_id search>>>> sss15: %s", product_id[0])
                                if product_id:
                                    move_val = {

                                        'product_id': product_id[0],
                                        'product_uom_qty': total_qty,  # line.product_qty,
                                        # 'qty_done': line.product_uom_qty,
                                        'location_id': loc_id[0],
                                        'location_dest_id': dest_loc_id,
                                        # 'product_qty':line.product_uom_qty,
                                        'product_uom': 1,  # line.product_uom.id,
                                        'name': line.name,
                                        'picking_id': picking_id,
                                        'company_id': 1,
                                        'date': picking.min_date,
                                        'date_deadline': picking.date_done or picking.min_date,
                                    }
                                    picking_vals['move_ids'].append(
                                        [0, False,
                                         {'product_id': product_id[0], 'product_uom_qty': total_qty, 'location_id': loc_id[0],'quantity_done':total_qty,
                                          'name': line.name,'date': picking.min_date,'date_deadline': picking.date_done or picking.min_date,
                                          'location_dest_id': dest_loc_id, 'product_uom': 1}])
                                    #move_id = models.execute_kw(db, sd_uid, password, 'stock.move', 'create', [move_val])

                                    #move_ids.append(move_id)
                        logging.warning("picking create value list>>>> sss15: %s", picking_vals)
                        picking_id = models.execute_kw(db, sd_uid, password, 'stock.picking', 'create', [picking_vals])
                        logging.warning("picking create picking id>>>> sss15: %s", picking_id)
                        models.execute_kw(db, sd_uid, password, 'stock.picking', 'action_confirm', [picking_id])
                        # models.execute_kw(db, sd_uid, password, 'stock.picking', 'action_set_quantities_to_reservation', [picking_id])

                        models.execute_kw(db, sd_uid, password, 'stock.picking', 'button_validate', [picking_id])
                        #models.execute_kw(db, sd_uid, password, 'stock.picking', 'action_done_custom', [picking_id])
                        models.execute_kw(db, sd_uid, password, 'stock.picking', 'write',
                                          [[picking_id], {'date_done': picking.date_done or picking.min_date,
                                                          'scheduled_date': picking.min_date,
                                                          'date_deadline': picking.min_date}])
                        self.write(cr, uid, picking.id, {'is_sync_odoo16': True}, context=context)
        except Exception as error:
            logging.warning("picking create value post error>>>> sss15: %s", error)
            if picking_id:
                try:
                    models.execute_kw(db, sd_uid, password, 'stock.picking', 'unlink', [picking_id])
                except Exception, e:
                    logging.warning("picking cancel unlink >>>> sss15: %s", e)
                    raise osv.except_osv(_('Error!'), _(error))
            raise osv.except_osv(_('Error!'), _(error))
        return result