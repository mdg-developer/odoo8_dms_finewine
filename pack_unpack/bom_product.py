# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp import tools, SUPERUSER_ID
from openerp.addons.product import _common


class bom_product(osv.osv):
    _name = 'bom.product'
    _description = "BOM Product"
    _inherit = ['mail.thread']
    _columns ={
        'name': fields.char('Name'),
        'code': fields.char('Reference', size=16),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the bills of material without removing it."),
        'position': fields.char('Internal Reference', help="Reference to a position in an external plan."),
        'product_tmpl_id': fields.many2one('product.template', 'Product', domain="[('type', '!=', 'service')]", required=True),
        'product_id': fields.many2one('product.product', 'Product Variant',
            domain="['&', ('product_tmpl_id','=',product_tmpl_id), ('type','!=', 'service')]",
            help="If a product variant is defined the BOM is available only for this product."),
        'bom_line_ids': fields.one2many('bom.product.line', 'bom_id', 'BoM Lines', copy=True),
        'product_qty': fields.float('Product Quantity', required=True, digits_compute=dp.get_precision('Product Unit of Measure')),
        'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True, help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control"),
        'date_start': fields.date('Valid From', help="Validity of this BoM. Keep empty if it's always valid."),
        'date_stop': fields.date('Valid Until', help="Validity of this BoM. Keep empty if it's always valid."),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of bills of material."),
        'product_rounding': fields.float('Product Rounding', help="Rounding applied on the product quantity."),
        'product_efficiency': fields.float('Manufacturing Efficiency', required=True, help="A factor of 0.9 means a loss of 10% during the production process."),
        'company_id': fields.many2one('res.company', 'Company', required=True),           
               }

    def _get_uom_id(self, cr, uid, *args):
        return self.pool["product.uom"].search(cr, uid, [], limit=1, order='id')[0]
    _defaults = {
        'active': lambda *a: 1,
        'product_qty': lambda *a: 1.0,
        'product_efficiency': lambda *a: 1.0,
        'product_rounding': lambda *a: 0.0,
#         'type': lambda *a: 'normal',
        'product_uom': _get_uom_id,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'bom.product', context=c),
    }
    _order = "sequence"

#------------------------------UNPACK------------------------------

    def _bom_explode_unpack(self, cr, uid, bom, product, factor, properties=None, level=0, routing_id=False, previous_products=None, master_bom=None, context=None):
        """ Finds Products and Work Centers for related BoM for manufacturing order.
        @param bom: BoM of particular product template.
        @param product: Select a particular variant of the BoM. If False use BoM without variants.
        @param factor: Factor represents the quantity, but in UoM of the BoM, taking into account the numbers produced by the BoM
        @param properties: A List of properties Ids.
        @param level: Depth level to find BoM lines starts from 10.
        @param previous_products: List of product previously use by bom explore to avoid recursion
        @param master_bom: When recursion, used to display the name of the master bom
        @return: result: List of dictionaries containing product details.
                 result2: List of dictionaries containing Work Center details.
        """
        
        uom_obj = self.pool.get("product.uom")
        #routing_obj = self.pool.get('mrp.routing')
        result=[]
        result2=[]
        if bom:
            result.append({
                    'name': product.product_id.name,
                    'product_id': product.product_id.id,
                    'product_qty': product.product_qty,
                    'product_uom': product.product_uom.id,
                    'product_uos_qty': product.product_uos_qty  or False,
                    'product_uos': product.product_uos or False,
                })
        
        return result, result2
    def _bom_find(self, cr, uid, product_tmpl_id=None, product_id=None, properties=None, context=None):
        """ Finds BoM for particular product and product uom.
        @param product_tmpl_id: Selected product.
        @param product_uom: Unit of measure of a product.
        @param properties: List of related properties.
        @return: False or BoM id.
        """
        if properties is None:
            properties = []
        if product_id:
            if not product_tmpl_id:
                product_tmpl_id = self.pool['product.product'].browse(cr, uid, product_id, context=context).product_tmpl_id.id
            domain = [
                '|',
                    ('product_id', '=', product_id),
                    '&',
                        ('product_id', '=', False),
                        ('product_tmpl_id', '=', product_tmpl_id)
            ]
        elif product_tmpl_id:
            domain = [('product_id', '=', False), ('product_tmpl_id', '=', product_tmpl_id)]
        else:
            # neither product nor template, makes no sense to search
            return False
        domain = domain + [ '|', ('date_start', '=', False), ('date_start', '<=', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                            '|', ('date_stop', '=', False), ('date_stop', '>=', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))]
        # order to prioritize bom with product_id over the one without
        ids = self.search(cr, uid, domain, order='product_id', context=context)
        # Search a BoM which has all properties specified, or if you can not find one, you could
        # pass a BoM without any properties
        bom_empty_prop = False
        for bom in self.pool.get('bom.product').browse(cr, uid, ids, context=context):
            if properties and not bom.property_ids:
                bom_empty_prop = bom.id
            else:
                return bom.id
            
        print 'empty_prop',bom_empty_prop
        return bom_empty_prop

    def _bom_explode(self, cr, uid, bom, product, factor, properties=None, level=0, routing_id=False, previous_products=None, master_bom=None, context=None):
        """ Finds Products and Work Centers for related BoM for manufacturing order.
        @param bom: BoM of particular product template.
        @param product: Select a particular variant of the BoM. If False use BoM without variants.
        @param factor: Factor represents the quantity, but in UoM of the BoM, taking into account the numbers produced by the BoM
        @param properties: A List of properties Ids.
        @param level: Depth level to find BoM lines starts from 10.
        @param previous_products: List of product previously use by bom explore to avoid recursion
        @param master_bom: When recursion, used to display the name of the master bom
        @return: result: List of dictionaries containing product details.
                 result2: List of dictionaries containing Work Center details.
        """
        uom_obj = self.pool.get("product.uom")
        #routing_obj = self.pool.get('mrp.routing')
        master_bom = master_bom or bom


        def _factor(factor, product_efficiency, product_rounding):
            factor = factor / (product_efficiency or 1.0)
            factor = _common.ceiling(factor, product_rounding)
            if factor < product_rounding:
                factor = product_rounding
            return factor

        factor = _factor(factor, bom.product_efficiency, bom.product_rounding)

        result = []
        result2 = []


        for bom_line_id in bom.bom_line_ids:
            if bom_line_id.date_start and bom_line_id.date_start > time.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or \
                bom_line_id.date_stop and bom_line_id.date_stop < time.strftime(DEFAULT_SERVER_DATETIME_FORMAT):
                    continue
            # all bom_line_id variant values must be in the product
            if bom_line_id.attribute_value_ids:
                if not product or (set(map(int,bom_line_id.attribute_value_ids or [])) - set(map(int,product.attribute_value_ids))):
                    continue

            if previous_products and bom_line_id.product_id.product_tmpl_id.id in previous_products:
                raise osv.except_osv(_('Invalid Action!'), _('BoM "%s" contains a BoM line with a product recursion: "%s".') % (master_bom.name,bom_line_id.product_id.name_get()[0][1]))

            quantity = _factor(bom_line_id.product_qty * factor, bom_line_id.product_efficiency, bom_line_id.product_rounding)
            bom_id = self._bom_find(cr, uid, product_id=bom_line_id.product_id.id, properties=properties, context=context)

            #If BoM should not behave like PhantoM, just add the product, otherwise explode further
            if bom_line_id:
                result.append({
                    'name': bom_line_id.product_id.name,
                    'product_id': bom_line_id.product_id.id,
                    'product_qty': quantity,
                    'product_uom': bom_line_id.product_uom.id,
                    'product_uos_qty': bom_line_id.product_uos and _factor(bom_line_id.product_uos_qty * factor, bom_line_id.product_efficiency, bom_line_id.product_rounding) or False,
                    'product_uos': bom_line_id.product_uos and bom_line_id.product_uos.id or False,
                })
            elif bom_id:
                all_prod = [bom.product_tmpl_id.id] + (previous_products or [])
                bom2 = self.browse(cr, uid, bom_id, context=context)
                # We need to convert to units/UoM of chosen BoM
                factor2 = uom_obj._compute_qty(cr, uid, bom_line_id.product_uom.id, quantity, bom2.product_uom.id)
                quantity2 = factor2 / bom2.product_qty
                res = self._bom_explode(cr, uid, bom2, bom_line_id.product_id, quantity2,
                    properties=properties, level=level + 10, previous_products=all_prod, master_bom=master_bom, context=context)
                result = result + res[0]
                result2 = result2 + res[1]
            else:
                raise osv.except_osv(_('Invalid Action!'), _('BoM "%s" contains a phantom BoM line but the product "%s" does not have any BoM defined.') % (master_bom.name,bom_line_id.product_id.name_get()[0][1]))
        print 'result',result
        print 'result2',result2
        return result, result2


    
    
    #-------------------------------------Unpack End -------------------------------
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        bom_data = self.read(cr, uid, id, [], context=context)
        default.update(name=_("%s (copy)") % (bom_data['name']))
        return super(bom_product, self).copy_data(cr, uid, id, default, context=context)

    def onchange_uom(self, cr, uid, ids, product_tmpl_id, product_uom, context=None):
        res = {'value': {}}
        if not product_uom or not product_tmpl_id:
            return res
        product = self.pool.get('product.template').browse(cr, uid, product_tmpl_id, context=context)
        uom = self.pool.get('product.uom').browse(cr, uid, product_uom, context=context)
        if uom.category_id.id != product.uom_id.category_id.id:
            res['warning'] = {'title': _('Warning'), 'message': _('The Product Unit of Measure you chose has a different category than in the product form.')}
            res['value'].update({'product_uom': product.uom_id.id})
        return res

    def unlink(self, cr, uid, ids, context=None):
        if self.pool['product.packing'].search(cr, uid, [('bom_id', 'in', ids), ('state', 'not in', ['done', 'cancel'])], context=context):
            raise osv.except_osv(_('Warning!'), _('You can not delete a Bill of Material with running manufacturing orders.\nPlease close or cancel it first.'))
        return super(bom_product, self).unlink(cr, uid, ids, context=context)

    def onchange_product_tmpl_id(self, cr, uid, ids, product_tmpl_id, product_qty=0, context=None):
        """ Changes UoM and name if product_id changes.
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        res = {}
        if product_tmpl_id:
            prod = self.pool.get('product.template').browse(cr, uid, product_tmpl_id, context=context)
            res['value'] = {
                'name': prod.name,
                'product_uom': prod.uom_id.id,
            }
        return res
bom_product()

class bom_product_line(osv.osv):
    _name = 'bom.product.line'
    _order = "sequence"

    def _get_child_bom_lines(self, cr, uid, ids, field_name, arg, context=None):
        """If the BOM line refers to a BOM, return the ids of the child BOM lines"""
        bom_obj = self.pool['bom.product']
        res = {}
        for bom_line in self.browse(cr, uid, ids, context=context):
            bom_id = bom_obj._bom_find(cr, uid,
                product_tmpl_id=bom_line.product_id.product_tmpl_id.id,
                product_id=bom_line.product_id.id, context=context)
            if bom_id:
                child_bom = bom_obj.browse(cr, uid, bom_id, context=context)
                res[bom_line.id] = [x.id for x in child_bom.bom_line_ids]
            else:
                res[bom_line.id] = False
        return res

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'product_uos_qty': fields.float('Product UOS Qty'),
        'product_uos': fields.many2one('product.uom', 'Product UOS', help="Product UOS (Unit of Sale) is the unit of measurement for the invoicing and promotion of stock."),
        'product_qty': fields.float('Product Quantity', required=True, digits_compute=dp.get_precision('Product Unit of Measure')),
        'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True,
            help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control"),
        
        'date_start': fields.date('Valid From', help="Validity of component. Keep empty if it's always valid."),
        'date_stop': fields.date('Valid Until', help="Validity of component. Keep empty if it's always valid."),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying."),
        'product_rounding': fields.float('Product Rounding', help="Rounding applied on the product quantity."),
        'product_efficiency': fields.float('Manufacturing Efficiency', required=True, help="A factor of 0.9 means a loss of 10% within the production process."),

        'bom_id': fields.many2one('bom.product', 'Parent BoM', ondelete='cascade', select=True, required=True),
        'attribute_value_ids': fields.many2many('product.attribute.value', string='Variants', help="BOM Product Variants needed form apply this line."),
        'child_line_ids': fields.function(_get_child_bom_lines, relation="bom.product.line", string="BOM lines of the referred bom", type="one2many")
    }

    def _get_uom_id(self, cr, uid, *args):
        return self.pool["product.uom"].search(cr, uid, [], limit=1, order='id')[0]
    _defaults = {
        'product_qty': lambda *a: 1.0,
        'product_efficiency': lambda *a: 1.0,
        'product_rounding': lambda *a: 0.0,
#         'type': lambda *a: 'normal',
        'product_uom': _get_uom_id,
    }
    _sql_constraints = [
        ('bom_qty_zero', 'CHECK (product_qty>0)', 'All product quantities must be greater than 0.\n' \
            'You should install the mrp_byproduct module if you want to manage extra products on BoMs !'),
    ]

    def onchange_uom(self, cr, uid, ids, product_id, product_uom, context=None):
        res = {'value': {}}
        if not product_uom or not product_id:
            return res
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        uom = self.pool.get('product.uom').browse(cr, uid, product_uom, context=context)
        if uom.category_id.id != product.uom_id.category_id.id:
            res['warning'] = {'title': _('Warning'), 'message': _('The Product Unit of Measure you chose has a different category than in the product form.')}
            res['value'].update({'product_uom': product.uom_id.id})
        return res

    def onchange_product_id(self, cr, uid, ids, product_id, product_qty=0, context=None):
        """ Changes UoM if product_id changes.
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        res = {}
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            res['value'] = {
                'product_uom': prod.uom_id.id,
                'product_uos_qty': 0,
                'product_uos': False
            }
            if prod.uos_id.id:
                res['value']['product_uos_qty'] = product_qty * prod.uos_coeff
                res['value']['product_uos'] = prod.uos_id.id
        return res

bom_product_line()
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------