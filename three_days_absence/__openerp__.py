# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
    'name': 'Three Days Absence',
    'version': '1.0',
    'category': 'HR',
    'sequence': 25,
    'summary': 'To Show Three Days Absence',
    'description': """
HR Section

""",
    'author': 'Seventh Computing',
    'website': 'http://www.7thcomputing.com',
    'depends': ['base',      
        'hr','attendance_data_import_v2'
 
    ],
    'data': [

       'views/threee_days_absence_view.xml',
    ],
    #'demo': ['hr_recruitment_demo.xml'],
    #'test': ['test/recruitment_process.yml'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
