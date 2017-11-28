import time
from openerp import netsvc
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class hr_department(osv.osv):
    
    _inherit = ['hr.department']
    _columns = {
       'hr_functional_units_id': fields.many2one('hr.functional.units', 'Functional Units', ondelete="cascade"),
       'analytic_id': fields.many2one('account.analytic.account', 'Analytic Account'),
       'salary_wages_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'salary_wages_debit': fields.many2one('account.account', 'Debit Account'),
       'salary_wages_credit': fields.many2one('account.account', 'Credit Account'),
       'ot_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'ot_debit': fields.many2one('account.account', 'Debit Account'),
       'ot_credit': fields.many2one('account.account', 'Credit Account'),
       'pdwe_salary_wages_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'pdwe_salary_wages_debit': fields.many2one('account.account', 'Debit Account'),
       'pdwe_salary_wages_credit': fields.many2one('account.account', 'Credit Account'),
       'pdwe_ot_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'pdwe_ot_debit': fields.many2one('account.account', 'Debit Account'),
       'pdwe_ot_credit': fields.many2one('account.account', 'Credit Account'),
       'sale_incentive_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'sale_incentive_debit': fields.many2one('account.account', 'Debit Account'),
       'sale_incentive_credit': fields.many2one('account.account', 'Credit Account'),
       'bonus_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'bonus_debit': fields.many2one('account.account', 'Debit Account'),
       'bonus_credit': fields.many2one('account.account', 'Credit Account'),
       'income_tax_emp_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'income_tax_emp_debit': fields.many2one('account.account', 'Debit Account'),
       'income_tax_emp_credit': fields.many2one('account.account', 'Credit Account'),
       'income_tax_employer_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'income_tax_employer_debit': fields.many2one('account.account', 'Debit Account'),
       'income_tax_employer_credit': fields.many2one('account.account', 'Credit Account'),
       'ssb_emp_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'ssb_emp_debit': fields.many2one('account.account', 'Debit Account'),
       'ssb_emp_credit': fields.many2one('account.account', 'Credit Account'),
       'ssb_employer_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'ssb_employer_debit': fields.many2one('account.account', 'Debit Account'),
       'ssb_employer_credit': fields.many2one('account.account', 'Credit Account'),
       'salary_wages_rule_allow': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'salary_wages_debit_allow': fields.many2one('account.account', 'Debit Account'),
       'salary_wages_credit_allow': fields.many2one('account.account', 'Credit Account'),
       'salary_wages_rule_deduct': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'salary_wages_debit_deduct': fields.many2one('account.account', 'Debit Account'),
       'salary_wages_credit_deduct': fields.many2one('account.account', 'Credit Account'),
       'ot_rule_allow': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'ot_debit_allow': fields.many2one('account.account', 'Debit Account'),
       'ot_credit_allow': fields.many2one('account.account', 'Credit Account'),
       'ot_rule_deduct': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'ot_debit_deduct': fields.many2one('account.account', 'Debit Account'),
       'ot_credit_deduct': fields.many2one('account.account', 'Credit Account'),
       'bonus_rule_allow': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'bonus_debit_allow': fields.many2one('account.account', 'Debit Account'),
       'bonus_credit_allow': fields.many2one('account.account', 'Credit Account'),
       'bonus_rule_deduct': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'bonus_debit_deduct': fields.many2one('account.account', 'Debit Account'),
       'bonus_credit_deduct': fields.many2one('account.account', 'Credit Account'),
       'sale_incentive_rule_allow': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'sale_incentive_debit_allow': fields.many2one('account.account', 'Debit Account'),
       'sale_incentive_credit_allow': fields.many2one('account.account', 'Credit Account'),
       'sale_incentive_rule_deduct': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'sale_incentive_debit_deduct': fields.many2one('account.account', 'Debit Account'),
       'sale_incentive_credit_deduct': fields.many2one('account.account', 'Credit Account'),
       'hr_business_units_id': fields.many2one('hr.business.units', 'Business Units', ondelete="cascade"),
       'mobile_allowance_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'mobile_allowance_debit': fields.many2one('account.account', 'Debit Account'),
       'mobile_allowance_credit': fields.many2one('account.account', 'Credit Account'),
       'fuel_allowance_rule': fields.many2one('hr.salary.rule', 'Salary Rule'),
       'fuel_allowance_debit': fields.many2one('account.account', 'Debit Account'),
       'fuel_allowance_credit': fields.many2one('account.account', 'Credit Account'),
    } 
    
hr_department()
