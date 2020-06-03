from openerp.osv import fields,osv
import requests
import json
import logging
import random

class res_partner(osv.osv):
    _inherit = 'res.partner'
    
    _columns = {
                'birthday': fields.date('Birthday'),
                'gender': fields.selection([('Male', 'Male'), ('Female', 'Female')], 'Gender'),
                'shop_name': fields.char('Shop/Business Name'),
            }   
          
    def send_otp_code(self, cr, uid, ids, mobile_phone, context=None):
        
        if mobile_phone:
            try: 
                headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}            
                sms_user= 'mdgpro'
                password= 'fcdaa533-e23d-4f9e-8480-416454b2dfc2'
                url='https://mpg-ids.mytel.com.mm/auth/realms/eis/protocol/openid-connect/token'
                payload = {'grant_type': 'client_credentials'}
                response = requests.post(url,headers=headers,auth=(sms_user, password), data=payload, verify=False)
                number = random.randint(1000,9999)         
                message = 'Dear customer,your OTP for registration is ' + str(number) + '.Use this code to register your account.'
                if response.status_code == 200:                
                    content = json.loads(response.content)
                    token = content['access_token'] 
                    header = {'Content-Type': 'application/json',
                              'Authorization': 'Bearer {0}'.format(token)}                    
                    sms_url = 'https://mytelapigw.mytel.com.mm/msg-service/v1.3/smsmt/sent'
                    sms_payload = {
                                   "source": "MDG",
                                   "dest": mobile_phone,
                                   "content": message 
                            }                 
                    response = requests.post(sms_url,  json = sms_payload, headers = header,verify=False)                
                    if response.status_code == 200:
                        return number              
            except Exception as e:         
                error_msg = 'Error Message: %s' % (e) 
                logging.error(error_msg)  
                return error_msg   
          
    def create_or_update_woo_customer(self, cr, uid, ids, customer_code=None, name=None,street=None,street2=None,township=None,state=None,mobile=None,phone=None,gender=None,birthday=None,email=None,partner_latitude=None,partner_longitude=None,sms=None,viber=None,shop_name=None,context=None):
        
        vals = {}
        township_obj = self.pool.get('res.township')
        city_obj = self.pool.get('res.city')
        partner_obj = self.pool.get('res.partner')
        outlettype_obj = self.pool.get('outlettype.outlettype')
        sale_channel_obj = self.pool.get('sale.channel')
        res_branch_obj = self.pool.get('res.branch')
        state_obj = self.pool.get('res.country.state')
        if not customer_code:
            vals['name']= name
            vals['street']= street
            vals['street2']= street2
            if township:
                township_value = township_obj.search(cr, uid, [('name', '=', township)], context=context)
                if township_value:
                    township_data = township_obj.browse(cr, uid, township_value, context=context)
                    vals['township']= township_data.id                    
                    city = city_obj.search(cr, uid, [('id', '=', township_data.city.id)], context=context)
                    if city:
                        city_data = city_obj.browse(cr, uid, city, context=context)
                        vals['city']= city_data.id
                    if township_data.delivery_team_id:
                        vals['delivery_team_id']= township_data.delivery_team_id.id
                    else:
                        if city_data.delivery_team_id:
                            vals['delivery_team_id']= city_data.delivery_team_id.id
            if state:                
                state_value = state_obj.search(cr, uid, [('name', '=', state)], context=context)
                if state_value:
                    state_data = state_obj.browse(cr, uid, state_value, context=context)
                    vals['state_id'] = state_data.id
            vals['sms'] = sms
            vals['viber'] = viber
            vals['shop_name'] = shop_name
            vals['partner_latitude'] = partner_latitude
            vals['partner_longitude'] = partner_longitude
            vals['mobile']= mobile
            vals['phone'] = phone
            vals['gender'] = gender
            vals['birthday'] = birthday
            vals['email'] = email
            vals['customer'] = True
            outlettype = outlettype_obj.search(cr, uid, [('name', '=', 'Site Registered')],context=context)            
            if outlettype:
                outlettype_data = outlettype_obj.browse(cr, uid, outlettype, context=context)
                vals['outlet_type'] = outlettype_data.id
            sale_channel = sale_channel_obj.search(cr, uid, [('code', '=', 'ECOM')], context=context)
            if sale_channel:
                sale_channel_data = sale_channel_obj.browse(cr, uid, sale_channel, context=context)
                vals['sales_channel'] = sale_channel_data.id                
            res_branch = res_branch_obj.search(cr, uid, [('branch_code', '=', 'TMW')], context=context)
            if res_branch:
                res_branch_data = res_branch_obj.browse(cr, uid, res_branch, context=context)
                vals['branch_id'] = res_branch_data.id                      
            result = partner_obj.create(cr, uid, vals, context=context)
            partner = partner_obj.search(cr, uid, [('id', '=', result)])
            if partner:
                partner_data = partner_obj.browse(cr, uid, partner, context=context)
                partner_obj.generate_customercode(cr, uid, [partner_data.id],partner_data,context=context)
            return result
        