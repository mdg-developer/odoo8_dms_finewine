-- Function: financial_report_monthly_balance_sheet(integer, integer, integer, integer, text)

-- DROP FUNCTION financial_report_monthly_balance_sheet(integer, integer, integer, integer, text);

CREATE OR REPLACE FUNCTION financial_report_monthly_balance_sheet(report_id integer, fiscal_year integer, start_period_id integer, end_period_id integer, state_cond text)
  RETURNS numeric AS
$BODY$
  DECLARE
    balance numeric;
    account_ids int[];
  --  opening_period int;
    temp_account_id int[];
    r account_account_financial_report%rowtype;
    sql text :=   'select
                    COALESCE(sum((aml.debit - aml.credit)),0)
                  from account_move_line aml,
                    account_period period,
                    account_fiscalyear fiscalyear,
                    account_move
                  WHERE
                    aml.period_id = period.id AND
                    aml.move_id = account_move.id AND
                    period.fiscalyear_id = fiscalyear.id';

  BEGIN

                       -- opening_period=(start_period_id-1);
                     -- select account_id from account_account_financial_report where report_line_id=report_id
                    FOR r IN select *  from account_account_financial_report where report_line_id=$1
                    LOOP
			select array_cat(account_ids,array_agg(id)) into account_ids from account_tree where r.account_id = ANY(PATH);
                    END LOOP;
                    --there is not account and return null for that
		     IF account_ids IS NULL THEN
			return null;
		     END IF;
                    IF account_ids IS NOT NULL THEN
                        sql := sql || ' AND aml.account_id in ('|| array_to_string(account_ids, ',') ||')';
	            END IF;
    IF  fiscal_year>0 THEN
      sql := sql || ' AND fiscalyear.id = $2';
    END IF;
    
    IF start_period_id >0 and  end_period_id >0 and start_period_id is not null and end_period_id is not null THEN
      sql := sql || ' AND aml.period_id >= ($3-1) and aml.period_id <= $4 ';
    END IF;
    
    IF $5 = 'posted' THEN
       sql := sql || ' AND account_move.state = $5';
    END IF;
    RAISE NOTICE ' SQL (%)', sql;
    EXECUTE sql into balance USING account_ids,fiscal_year,start_period_id,end_period_id,state_cond;
    IF balance < 0 THEN
    balance = balance * -1;
    END IF;

   return balance;
  END;
  $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION financial_report_monthly_balance_sheet(integer, integer, integer, integer, text)
  OWNER TO postgres;

  -----------------------------------------------------------------------------------------------------------------------------------------------
  
  
  -- Function: financial_report_monthly_balance(integer, integer, integer, text)

-- DROP FUNCTION financial_report_monthly_balance(integer, integer, integer, text);

CREATE OR REPLACE FUNCTION financial_report_monthly_balance(report_id integer, fiscal_year integer, period_id integer, state_cond text)
  RETURNS numeric AS
$BODY$
  DECLARE
    balance numeric;
    account_ids int[];
    temp_account_id int[];
    r account_account_financial_report%rowtype;
    sql text :=   'select
                    COALESCE(sum((aml.debit - aml.credit)),0)
                  from account_move_line aml,
                    account_period period,
                    account_fiscalyear fiscalyear,
                    account_move
                  WHERE
                    aml.period_id = period.id AND
                    aml.move_id = account_move.id AND
                    period.fiscalyear_id = fiscalyear.id';

  BEGIN


                     -- select account_id from account_account_financial_report where report_line_id=report_id
                    FOR r IN select *  from account_account_financial_report where report_line_id=$1
                    LOOP
			select array_cat(account_ids,array_agg(id)) into account_ids from account_tree where r.account_id = ANY(PATH);
                    END LOOP;
                    --there is not account and return null for that
		     IF account_ids IS NULL THEN
			return null;
		     END IF;
                    IF account_ids IS NOT NULL THEN
                        sql := sql || ' AND aml.account_id in ('|| array_to_string(account_ids, ',') ||')';
	            END IF;
    IF  fiscal_year>0 THEN
      sql := sql || ' AND fiscalyear.id = $2';
    END IF;

    
    IF period_id >0  and period_id is not null THEN
      sql := sql || ' AND aml.period_id = $3 ';
    END IF;
    
    
    IF $4 = 'posted' THEN
       sql := sql || ' AND account_move.state = $4';
    END IF;
    RAISE NOTICE ' SQL (%)', sql;
    EXECUTE sql into balance USING account_ids,fiscal_year,period_id,state_cond;
    IF balance < 0 THEN
    balance = balance * -1;
    END IF;

   return balance;
  END;
  $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION financial_report_monthly_balance(integer, integer, integer, text)
  OWNER TO openerp;
