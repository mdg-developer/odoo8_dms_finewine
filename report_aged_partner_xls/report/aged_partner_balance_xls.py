# -*- coding: utf-8 -*-
###############################################################################
#
#   report_aged_partner_xls for Odoo
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import xlwt
from datetime import datetime
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.addons.account_financial_report_webkit.report.aged_partner_balance \
    import AccountAgedTrialBalanceWebkit
from openerp.tools.translate import _

class aged_partner_balance_xls(report_xls):
    column_sizes = [17, 17, 17, 17, 17, 17, 17, 17, 17, 17]

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        ws = wb.add_sheet(_p.report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']
        
        branch_obj = self.pool.get('res.branch')
        branch_name = ''        
        if _p.branch_id:
            
            for branch in branch_obj.browse(self.cr,self.uid,_p.branch_id,context=None):
                branch_name += str(branch.branch_code) + ','
            branch_name = branch_name[:-1]    
        else:
            branch_name = 'All' 
        
        account_obj = self.pool.get('account.account')
        account_code = ''        
        if _p.account_id:
            
            for account in account_obj.browse(self.cr,self.uid,_p.account_id,context=None):
                account_code += str(account.code) + ','
            account_code = account_code[:-1]    
        else:
            account_code = 'All'     
        # cf. account_report_general_ledger.mako
        initial_balance_text = {'initial_balance': _('Computed'),
                                'opening_balance': _('Opening Entries'),
                                False: _('No')}

        # Title
        cell_style = xlwt.easyxf(_xs['xls_title'])
        report_name = ' - '.join([_p.report_name.upper(),
                                 _p.company.partner_id.name,
                                 _p.company.currency_id.name])
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style)

        # write empty row to define column sizes
        c_sizes = self.column_sizes
        c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None)
                   for i in range(0, len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, set_column_size=True)

        # Header Table
        cell_format = _xs['bold'] + _xs['fill_blue'] + _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_specs = [
            ('coa', 2, 0, 'text', _('Chart of Account')),
            ('fy', 1, 0, 'text', _('Fiscal Year')),
            ('df', 2, 0, 'text', _p.filter_form(data) ==
             'filter_date' and _('Dates Filter') or _('Periods Filter')),
            ('cd', 1, 0, 'text', _('Clearance Date')),
            ('af', 2, 0, 'text', _('Accounts Filter')),
            ('aaf', 2, 0, 'text', _('Analytic Accounts Filter')),
            ('tm', 2, 0, 'text', _('Target Moves')),
            ('br', 2, 0, 'text', _('Branch')),

        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style_center)

        cell_format = _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_specs = [
            #('coa', 2, 0, 'text', _p.chart_account.name),
            ('coa', 2, 0, 'text', account_code),
            ('fy', 1, 0, 'text', _p.fiscalyear.name if _p.fiscalyear else '-'),
        ]
        df = _('From') + ': '
        if _p.filter_form(data) == 'filter_date':
            df += _p.start_date if _p.start_date else u''
        else:
            df += _p.start_period.name if _p.start_period else u''
        df += ' ' + _('To') + ': '
        if _p.filter_form(data) == 'filter_date':
            df += _p.stop_date if _p.stop_date else u''
        else:
            df += _p.stop_period.name if _p.stop_period else u''
        c_specs += [
            ('df', 2, 0, 'text', df),
            ('cd', 1, 0, 'text', _p.date_until),
            ('af', 2, 0, 'text', _p.display_partner_account(data)),
            ('aaf', 2, 0, 'text', _p.analytic_accounts(data) and ', '.join(
                [analytic.code for analytic in _p.analytic_accounts(data)]) or _('All')),
            ('tm', 2, 0, 'text', _p.display_target_move(data)),
            #('br', 2, 0, 'text', _p.branch_id[1] if _p.branch_id else u''),
            ('br', 2, 0, 'text', branch_name),
            
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style_center)
        ws.set_horz_split_pos(row_pos)
        row_pos += 1

        # Column Title Row
        cell_format = _xs['bold']
        c_title_cell_style = xlwt.easyxf(cell_format)

        # Column Header Row
        cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        c_hdr_cell_style = xlwt.easyxf(cell_format)
        c_hdr_cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
        c_hdr_cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_hdr_cell_style_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        cell_format = _xs['italic'] + _xs['borders_all']
        c_init_cell_style = xlwt.easyxf(cell_format)
        c_init_cell_style_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        c_init_cell_style_decimal_bold = xlwt.easyxf(
            cell_format + _xs['right'] + _xs['bold'],
            num_format_str=report_xls.decimal_format)
        c_specs = [
            ('partner', 2, 0, 'text', _('Partner'), None, c_hdr_cell_style),
            ('code', 1, 0, 'text', _('Code'), None, c_hdr_cell_style),
            ('balance', 1, 0, 'text', _('Balance'), None, c_hdr_cell_style),
        ]
        cnt = 0
        for range_title in _p.ranges_titles:
            cnt += 1
            c_specs.append(('classification' + str(cnt), 1, 0, 'text', _(range_title), None, c_hdr_cell_style))
        if _p.amount_currency(data):
            c_specs += [
                    ('cur_bal', 1, 0, 'text', _('Cur Bal'), None, c_hdr_cell_style),
                    ('curcode', 1, 0, 'text', _('Cur Code'), None, c_hdr_cell_style)
                ]

        c_hdr_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])

        # cell styles for aged lines
        ll_cell_format = _xs['borders_all']
        ll_cell_style = xlwt.easyxf(ll_cell_format)
        ll_cell_style_center = xlwt.easyxf(ll_cell_format + _xs['center'])
        ll_cell_style_date = xlwt.easyxf(
            ll_cell_format + _xs['left'],
            num_format_str=report_xls.date_format)
        ll_cell_style_decimal = xlwt.easyxf(
            ll_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        cnt = 0
        for acc in objects:
            if _p.agged_lines_accounts[acc.id]:
                cnt += 1
                cumul_debit = 0.0
                cumul_credit = 0.0
                cumul_balance = 0.0
                cumul_balance_curr = 0.0
                c_specs = [
                    ('acc_title', 11, 0, 'text',
                     ' - '.join([acc.code, acc.name])),
                ]
                row_data = self.xls_row_template(
                    c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(
                    ws, row_pos, row_data, c_title_cell_style)
                row_pos += 1
                row_pos = self.xls_write_row(ws, row_pos, c_hdr_data)
                row_start = row_pos

                for partner_name, p_id, p_ref, p_name in _p.partners_order[acc.id]:
                    if _p.agged_lines_accounts[acc.id].get(p_id):
                        line = _p.agged_lines_accounts[acc.id][p_id]
                        c_specs = [
                            ('partner', 2, 0, 'text', _(partner_name or '')),
                            ('code', 1, 0, 'text', _(p_ref or '')),
                            ('balance', 1, 0, 'number', line.get('balance'), None, c_init_cell_style_decimal)
                        ]

                        count = 0
                        for classif in _p.ranges:
                            count += 1
                            c_specs.append(('classification' + str(count), 1, 0, 'number', line['aged_lines'][classif] or 0.0, None, c_init_cell_style_decimal))
  
                        if _p.amount_currency(data):
                            c_specs += [
                                        ('cur_bal', 1, 0, 'number', line.get('amount_currency'), None, c_init_cell_style_decimal),
                                        ('curcode', 1, 0, 'text', line.get('currency_code'), None, c_init_cell_style)
                            ]

                        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                        row_pos = self.xls_write_row(ws, row_pos, row_data)
                
                percents = _p.agged_percents_accounts[acc.id]
                totals = _p.agged_totals_accounts[acc.id]
                c_specs = [
                            ('total', 3, 0, 'text', _('Total'), None, c_hdr_cell_style),
                            ('balance', 1, 0, 'number', totals['balance'], None, c_init_cell_style_decimal_bold)
                        ]

                count = 0
                for classif in _p.ranges:
                    count += 1
                    c_specs.append(('classification' + str(count), 1, 0, 'number', totals[classif] or 0.0, None, c_init_cell_style_decimal_bold))

                row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(ws, row_pos, row_data)
                c_specs = [('percents', 4, 0, 'text', _('Percents'), None, c_hdr_cell_style)]

                count = 0
                for classif in _p.ranges:
                    count += 1
                    c_specs.append(('classification' + str(count), 1, 0, 'number', percents[classif]or 0.0, None, c_init_cell_style_decimal_bold))

                row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(ws, row_pos, row_data)
                row_pos += 1

aged_partner_balance_xls('report.account.account_report_aged_partner_balance_xls',
                   'account.account',
                   parser=AccountAgedTrialBalanceWebkit)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: