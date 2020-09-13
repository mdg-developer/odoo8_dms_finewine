from openerp import models,fields,api
import requests

class res_partner(models.Model):
    _inherit="res.partner"
    woo_company_name_ept=fields.Char("Company Name")
    woo_customer_id=fields.Char("Woo Customer Id")
    
    @api.model
    def import_woo_customers(self,instance=False):        
        instances=[]
        transaction_log_obj=self.env["woo.transaction.log"]
        instances.append(instance)
        sale_order_obj=self.env['sale.order']
        
        for instance in instances:            
            wcapi = instance.connect_in_woo()
            response = wcapi.get('customers')
            if not isinstance(response,requests.models.Response):                
                transaction_log_obj.create({'message': "Import Customers \nResponse is not in proper format :: %s"%(response),
                                             'mismatch_details':True,
                                             'type':'customer',
                                             'woo_instance_id':instance.id
                                            })
                continue                                    
            if response.status_code not in [200,201]:
                message = "Error in Import Customers %s"%(response.content)                        
                transaction_log_obj.create(
                                    {'message':message,
                                     'mismatch_details':True,
                                     'type':'customer',
                                     'woo_instance_id':instance.id
                                    })
                continue
            
            response_data = response.json()
            billing = ''
            shipping = ''
            woo_customers = []
            
            if instance.woo_version == 'old':                
                woo_customers = response_data.get("customers")
                billing="billing_address"
                shipping="shipping_address"
            elif instance.woo_version == 'new':
                woo_customers = response_data
                billing="billing"
                shipping="shipping"
          
            for customer in woo_customers:
                woo_customer_id = customer.get('id',False)                
                partner=customer.get(billing,False) and sale_order_obj.create_or_update_woo_customer(woo_customer_id,customer.get(billing), False, False,False,instance)
                if partner:
                    shipping_address=customer.get(shipping,False) and sale_order_obj.create_or_update_woo_customer(False,customer.get(shipping), False,partner.id,'delivery',instance) or partner
                