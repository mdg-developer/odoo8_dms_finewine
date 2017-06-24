# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name' : 'Product Pricelists',
    'version' : '1.0',
    'author': 'seventh computing',
    'website': 'http://www.7thcomputing.com',
    'category' : 'Product',
    'depends' : ["base", "sale", "product", "product_product"],
    'description': """
    Product Pricelists for OpenERP
    = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    Features:
        1.Product Main group adding in product pricelist.
    
 
    """,
    'data': [
 'views/product_pricelist_view.xml',
 'views/product_pricelist_item_view.xml'
                ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
