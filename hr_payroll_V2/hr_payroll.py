# -*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
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

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import calendar
from openerp.tools.safe_eval import safe_eval as eval

class hr_payslip_worked_days(osv.osv):
    '''
    Payslip Worked Days
    '''
    _inherit = 'hr.payslip.worked_days'
    _description = 'Payslip Worked Days'
    _columns = {  
        'total_month_day': fields.float('Total Month Days'),
        'working_month': fields.float('Working Month'),
        }  
    
class hr_payslip_customize(osv.osv):
    '''
    Payslip Worked Time
    '''
    _inherit = 'hr.payslip'
    _columns = {  
        'total_month_day': fields.float('Total Month Days'),
        'working_month': fields.float('Working Month'),
        }
    
    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = []
        contract_obj = self.pool.get('hr.contract')
        rule_obj = self.pool.get('hr.salary.rule')
        financial_year = 0
        total_income = 0
        tax_paid = 0   
        payroll_total_income = 0
        income_tax = 0
        # get Employee data
        cr.execute("select employee_id,date_start from hr_contract where id=%s", (contract_ids))
        emp_data = cr.fetchone()
        employee_id = emp_data[0]
        initial_date =emp_data[1]
        
        cr.execute("select fiscalyear_id from account_period where date_start <=%s and date_stop >= %s", (date_from, date_to,))
        fiscalyear_id = cr.fetchone()
        if fiscalyear_id:
            fiscalyear_id = fiscalyear_id[0]
            cr.execute("select financial_year,total_income,tax_paid  from hr_employee he ,account_period ap where ap.id=%s and he.id=%s", (fiscalyear_id, employee_id,))
            previous_tax = cr.fetchone()
            if previous_tax:
                financial_year = previous_tax[0]
                total_income = previous_tax[1]
                tax_paid = previous_tax[2]
            cr.execute ("select sum(hpl.total) as total_income from hr_payslip h , hr_payslip_line hpl ,(select date_start,date_stop from account_period where fiscalyear_id = %s) f where hpl.slip_id =h.id and h.date_from=f.date_start and h.date_to=f.date_stop and state ='done'and code = 'NET'  and h.employee_id=%s ", (fiscalyear_id, employee_id,))    
            payroll_total_income = cr.fetchone()
            if payroll_total_income:
                payroll_total_income = payroll_total_income[0]      
            cr.execute ("select sum(hpl.total) as income_tax from hr_payslip h , hr_payslip_line hpl ,(select date_start,date_stop from account_period where fiscalyear_id = %s) f where hpl.slip_id =h.id and h.date_from=f.date_start and h.date_to=f.date_stop and state ='done'and code = 'ICT'  and h.employee_id=%s ", (fiscalyear_id, employee_id,))             
            income_tax = cr.fetchone()
            if income_tax:
                income_tax = income_tax[0]      
        structure_ids = contract_obj.get_all_structures(cr, uid, contract_ids, context=context)
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        cr.execute('select sum(fine_amount) from hr_fine where lost_date between %s and %s and employee_id= %s', (date_from, date_to, employee_id,))
        fine_data = cr.fetchone()
        if fine_data:
            fine_amount = fine_data[0]
        else:
            fine_amount = 0.0
        cr.execute("select sum(early) as early_time ,sum(late) as late_min  from attendance_data_import where date between %s and  %s and  employee_id=%s", (date_from, date_to,employee_id,))
        total_minus = cr.fetchone()    
        if total_minus:
            early_minus = total_minus[0]
            late_min = total_minus[1]
        else:
            early_minus = 0
            late_min = 0         
        cr.execute("select sum(ot_time) as ot_minus  from attendance_data_import where date between %s and  %s and  employee_id=%s and state ='approve'", (date_from, date_to,employee_id,))
        total_ot = cr.fetchone()   
        if total_ot:
            ot_minus = total_ot[0]
        else:
            ot_minus = 0
        cr.execute("select COALESCE( sum(normal),0) as normal  from attendance_data_import where \
        date between %s and  %s and date not in (SELECT the_day ::date FROM  generate_series(%s::date, %s  ::date, '1 day') d(the_day) \
        WHERE  extract('ISODOW' FROM the_day)= 7)\
        and date not in (select date from hr_holidays_public_line where date between %s and  %s )\
        and date not in (select generate_series(hh.date_from::date, hh.date_to::date, '1 day')::date as date from hr_holidays hh,hr_holidays_status ss  where hh.holiday_status_id = ss.id  and hh.employee_id =%s and ss.name !='Unpaid' and hh.date_to between  %s and %s )\
        and absent =true and employee_id=%s",(date_from, date_to,date_from, date_to,date_from, date_to,employee_id,date_from, date_to,employee_id,))
        absent_data =cr.fetchone()
        if absent_data:
            absent_count=absent_data[0]
        cr.execute("select COALESCE( sum(normal) ,0) as total_working_day  from attendance_data_import where \
        date between %s and  %s and date not in (SELECT the_day ::date FROM  generate_series(%s::date, %s  ::date, '1 day') d(the_day) \
        WHERE  extract('ISODOW' FROM the_day) = 7 )\
        and date not in ( select date from hr_holidays_public_line where date between %s and  %s )\
        and date not in (select generate_series(date_from::date, date_to::date, '1 day')::date as date from hr_holidays where  employee_id =%s and date_to between  %s and %s )\
        and absent != true and employee_id=%s",(date_from, date_to,date_from, date_to,date_from, date_to,employee_id,date_from, date_to,employee_id,))
        present_data =cr.fetchone()
        cr.execute("select  COALESCE( sum(number_of_days_temp - floor(number_of_days_temp)))  as leave_count from hr_holidays  where  employee_id =%s and date_to between %s and %s ",(employee_id,date_from, date_to,))
        leave_half_count =cr.fetchone()[0]
        if leave_half_count is None:
            leave_half_count=0
        cr.execute("select COALESCE( sum(normal),0) from attendance_data_import where lower(timetable)= 'afternoon' and absent =true  and extract('ISODOW' FROM date)= 6  and employee_id=%s and date between  %s  and  %s ",(employee_id,date_from, date_to,))        
        sat_data =cr.fetchone()[0]
        if present_data:
            present_count=present_data[0]+ sat_data+leave_half_count
        else:
            present_count=0
        con_date  = date_from
        before_day=0
        if initial_date > date_from:
            con_date =initial_date
            cr.execute("SELECT TRUNC(DATE_PART('day',  %s::timestamp - %s::timestamp))",(initial_date,date_from,))
            before_day=cr.fetchone()[0]
        cr.execute( "select sum(count) as public_count from (SELECT count(the_day ::date) FROM  generate_series(%s::date, %s ::date, '1 day') d(the_day) WHERE  extract('ISODOW' FROM the_day)= 7 \
                        union all  \
                        select count(date) from hr_holidays_public_line where date between %s and %s  )A ",(con_date, date_to,con_date,date_to, ))   
        holiday_data =cr.fetchone()
        if holiday_data:
            holiday_count=holiday_data[0]        
        else:
            holiday_count=0        
        cr.execute(" select COALESCE( sum(duration),0) from hr_temporary_out where employee_id= %s and date between %s and %s",(employee_id,date_from, date_to,))      
        temporary_min =cr.fetchone()[0]
        cr.execute(" select COALESCE(sum(amount),0) from hr_efficiency_value where employee_id= %s and code ='EBS' and date between %s and %s",(employee_id,date_from, date_to,))      
        efficiency_value =cr.fetchone()[0]        
        cr.execute(" select COALESCE(sum(amount),0) from hr_efficiency_value where employee_id= %s and code ='QLB' and date between %s and %s",(employee_id,date_from, date_to,))      
        quality_value =cr.fetchone()[0]       
        cr.execute(" select COALESCE(sum(amount),0) from hr_efficiency_value where employee_id= %s and code ='PFB' and date between %s and %s",(employee_id,date_from, date_to,))      
        performance_bonus =cr.fetchone()[0]               
                 
        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
            for rule in rule_obj.browse(cr, uid, sorted_rule_ids, context=context):
                if rule.input_ids:
                    for input in rule.input_ids:
                        if input.code == 'ETI':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':total_income,
                               'contract_id': contract.id,
                              }
                        else:
                            inputs = {
                                     'name': input.name,
                                     'code': input.code,
                                     'amount':0.0,
                                     'contract_id': contract.id,
                                }
                        if input.code == 'PET':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':tax_paid,
                               'contract_id': contract.id,
                              }
                        if input.code == 'PPT':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':income_tax,
                               'contract_id': contract.id,
                              } 
                        if input.code == 'PTI':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':payroll_total_income,
                               'contract_id': contract.id,
                              }                         
                      
                        if input.code == 'FINE':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':fine_amount,
                               'contract_id': contract.id,
                              }                          
                        if input.code == 'OM':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':ot_minus,
                               'contract_id': contract.id,
                              }                
                        if input.code == 'EM':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':early_minus,
                               'contract_id': contract.id,
                              }                
                        if input.code == 'LM':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':late_min,
                               'contract_id': contract.id,
                              }                 
                        if input.code == 'AC':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':absent_count,
                               'contract_id': contract.id,
                              }        
                        if input.code == 'PC':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':present_count,
                               'contract_id': contract.id,
                              }        
                        if input.code == 'HC':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':holiday_count,
                               'contract_id': contract.id,
                              }         
                        if input.code == 'GPTO':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':temporary_min,
                               'contract_id': contract.id,
                              }                     
                        if input.code == 'BDC':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':before_day,
                               'contract_id': contract.id,
                              }  
                        if input.code == 'EBS':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':efficiency_value,
                               'contract_id': contract.id,
                              }                
                        if input.code == 'QLB':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':quality_value,
                               'contract_id': contract.id,
                              }                                        
                        if input.code == 'PFB':
                            inputs = {
                               'name': input.name,
                               'code': input.code,
                               'amount':performance_bonus,
                               'contract_id': contract.id,
                              }                                                                                                                                                                                                                                                                                             
                        res += [inputs]
        return res
    
    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        day_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        day_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        month_days = calendar.monthrange(day_from.year, day_from.month)[1]   
        print 'month_days', month_days
        cr.execute('select employee_id,date_start from hr_contract where id = %s', (contract_ids))
        employee_data = cr.fetchone() 
        if  employee_data:
            employee_id=employee_data[0]
            initial_date=employee_data[1]
        working_month = 0
        cr.execute("SELECT EXTRACT(MONTH FROM %s::date) as next_month", (date_from,))
        next_month = cr.fetchone()[0]
        
        if int(next_month) is 1 or int(next_month) is 2 or int(next_month) is 3:
            cr.execute("SELECT EXTRACT(YEAR FROM %s::date) as next_year", (date_from,))
            next_year = cr.fetchone()        
        else:
            cr.execute("SELECT EXTRACT(YEAR FROM %s::date)+1 as next_year", (date_from,))
            next_year = cr.fetchone()
        if next_year[0] is not None: 
            next_year = int(next_year[0])       
              
            cr.execute("SELECT (date_part('year',age('%s-03-01', %s)) * 12 )+date_part('month',age('%s-04-01', %s)) as w_month", (next_year, date_to, next_year, date_to,))
            w_month = cr.fetchone()
            if w_month:
                if w_month[0] >= 12:
                    working_month = 12;
                else:
                    working_month = w_month[0]
            print 'working_month', working_month, next_year             
        def was_on_leave(employee_id, datetime_day, context=None):
            # res = False
            leave_type = False
            day_temp = False
            day = datetime_day.strftime("%Y-%m-%d")
            holiday_ids = self.pool.get('hr.holidays').search(cr, uid, [('state', '=', 'validate'), ('employee_id', '=', employee_id), ('type', '=', 'remove'), ('date_from', '<=', day), ('date_to', '>=', day)])
            if holiday_ids:
                leave_type = self.pool.get('hr.holidays').browse(cr, uid, holiday_ids, context=context)[0].holiday_status_id.name
                day_temp = self.pool.get('hr.holidays').browse(cr, uid, holiday_ids, context=context)[0].number_of_days_temp
            return leave_type, day_temp

        res = []
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            if not contract.working_hours:
                # fill only if the contract as a working schedule linked
                continue
            # add function return from store procedure                                  
            day_from = datetime.strptime(date_from, "%Y-%m-%d")
            day_to = datetime.strptime(date_to, "%Y-%m-%d")
            nb_of_days = (day_to - day_from).days + 1
            
            attendances = {
                 'name': _("Normal Working Days paid at 100%"),
                 'sequence': 0,
                 'code': 'WORK100',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'number_of_minutes':0.0,
                'total_month_day':nb_of_days,
                'working_month':working_month,
                 'contract_id': contract.id,
            }
            leaves = {}
            day_from = datetime.strptime(date_from, "%Y-%m-%d")
            day_to = datetime.strptime(date_to, "%Y-%m-%d")

            for day in range(0, nb_of_days):
                working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + timedelta(days=day), context)
                cr.execute('select sum(number_of_days)*-1 as leave from hr_holidays where number_of_days<0 and employee_id=%s and date_from between %s and %s', (contract.employee_id.id, day_from, day_to))   
                leave = cr.fetchone()
                if leave:
                    leave_day = leave[0]
                    if leave_day is None:
                        leave_day = 0.0
                else:
                    leave_day = 0.0
                if working_hours_on_day:
                    # the employee had to work
                    leave_type, day_temp = was_on_leave(contract.employee_id.id, day_from + timedelta(days=day), context=context)
                    if leave_type:
                        # if he was on leave, fill the leaves dict
                        if leave_type in leaves and day_temp != 0.5:
                            leaves[leave_type]['number_of_days'] += 1
                            leaves[leave_type]['number_of_hours'] += working_hours_on_day
                        elif leave_type in leaves  and day_temp == 0.5 :

                            leaves[leave_type]['number_of_days'] += day_temp
                            leaves[leave_type]['number_of_hours'] += working_hours_on_day / 2   
                             
                        elif day_temp == 0.5:

                            leaves[leave_type] = {
                                'name': leave_type,
                                'sequence': 5,
                                'code': leave_type,
                                'number_of_days': day_temp,
                                'number_of_hours': working_hours_on_day / 2,
                                'contract_id': contract.id,
                            }
                        elif day_temp != 0.5:
                            leaves[leave_type] = {
                                'name': leave_type,
                                'sequence': 5,
                                'code': leave_type,
                                'number_of_days': 1.0,
                                'number_of_hours': working_hours_on_day,
                                'contract_id': contract.id,
                            }
                    else:
                        attendances['number_of_days'] += 1.0
                        attendances['number_of_hours'] += working_hours_on_day
            leaves = [value for key, value in leaves.items()]
            cr.execute("select count(id) from hr_holidays_public_line where date between %s and  %s ",(day_from,day_to,))
            public_count =cr.fetchone()
            if public_count:
                public_count=public_count[0]
            else:
                public_count=0
            before_day=0
            sun_count=0
            if initial_date > date_from:
                cr.execute("SELECT TRUNC(DATE_PART('day',  %s::timestamp - %s::timestamp))",(initial_date,date_from,))
                before_day=cr.fetchone()[0]
                cr.execute("SELECT count(the_day ::date) as sat_count FROM generate_series(%s::date, %s ::date, '1 day') d(the_day)  WHERE  extract('ISODOW' FROM the_day) = 7  ",(day_from,initial_date,))
                sun_count =cr.fetchone()[0]
                print 'sun_count',sun_count
               
            cr.execute("SELECT count(the_day ::date) as sat_count FROM generate_series(%s::date, %s ::date, '1 day') d(the_day)  WHERE  extract('ISODOW' FROM the_day) = 6  ",(day_from,day_to,))
            sat_count =cr.fetchone()
            if sat_count:
                sat_count=sat_count[0]/2
            else:
                sat_count=0    
            cr.execute("select  COALESCE( sum(number_of_days_temp - floor(number_of_days_temp)))  as leave_count from hr_holidays  where  employee_id =%s and date_to between %s and %s ",(contract.employee_id.id,date_from, date_to,))
            leave_half_count =cr.fetchone()[0]
            if leave_half_count is None:
                leave_half_count=0            
            attendances['number_of_days'] -= (public_count + (before_day -sun_count))
            attendances['number_of_days'] += leave_half_count
            res += [attendances] + leaves 
        return res