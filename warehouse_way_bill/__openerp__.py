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

{
    'name': 'Way Bill',
    'version': '1.1',
    'author': '7th Computing',
    'summary': 'Way Bill',
    'description': """

Way Bill' Module
===============================

    """,
    'website': 'https://www.odoo.com/page/warehouse',
    'depends': ['base', 'sale', 'stock', 'warehouse_transfer_request', 'stock_split_picking'],
    'category': 'stock',
    'sequence': 16,
    'data': [
        'views/sequence.xml',
        'views/way_bill_view.xml',
        'views/stock_picking_view.xml',
        'reports/mdg_custom_layouts.xml',
        'reports/qweb_view.xml',
        'reports/report_way_bill.xml',
    ],
    'test': [

    ],
    'installable': True,
}
