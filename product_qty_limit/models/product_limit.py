from openerp.osv import fields, osv
import logging
import json
import requests
from requests.structures import CaseInsensitiveDict
import base64
from openerp.osv.orm import except_orm
from openerp.tools.translate import _

class product_limit(osv.osv):
    _name = "product.limit"
    _columns = {
        'state_id': fields.many2one('res.country.state', 'State'),
        'city_id': fields.many2one('res.city', 'City'),
        'township_ids': fields.many2many('res.township', 'product_limit_township_rel', 'product_limit_id', 'township_id', 'Township'),
        'product_id': fields.many2one('product.template', 'Product'),
        'max_qty':fields.integer('Max Qty'),
        'is_sync_woo': fields.boolean('Is Sync Woo', default=False),
    }

    def write(self, cr, uid, ids, vals, context=None):
        data = self.browse(cr,uid,ids[0])
        if data.is_sync_woo == True:
            vals['is_sync_woo']=False
        res = super(product_limit, self).write(cr, uid, ids, vals, context=context)
        return res

    def sync_to_woo(self, cr, uid, ids, context=None):

        data = self.browse(cr, uid, ids[0])
        if data.is_sync_woo != True:
            woo_instance_obj = self.pool.get('woo.instance.ept')
            product_limit_obj = self.pool.get('product.limit')
            instance = woo_instance_obj.search(cr, uid, [('state', '=', 'confirmed')], limit=1)
            if instance:
                instance_obj = woo_instance_obj.browse(cr, uid, instance)
                url = instance_obj.host + "/wp-json/auth-api/v1/odoo/stocks/stock_data_update"
                headers = CaseInsensitiveDict()
                login_info = instance_obj.admin_username + ":" + instance_obj.admin_password
                login_info_bytes = login_info.encode('ascii')
                base64_bytes = base64.b64encode(login_info_bytes)
                logging.warning("Check base64_bytes: %s", base64_bytes)
                headers["Authorization"] = "Basic " + base64_bytes
                headers["Content-Type"] = "application/json"
                for line in data.township_ids:
                    branch_code = line.branch_id.branch_code
                    city = data.city_id.name
                    township = line.name
                    product_code = data.product_id.default_code
                    limit_data = {
                                    "branch_code": str(branch_code),
                                    "city": str(city),
                                    "township": str(township),
                                    "product_lists": [
                                                    {
                                                        "product_sku": str(product_code),
                                                        "max_stock": data.max_qty
                                                    }
                                                ]
                                }
                    logging.warning("Check limit_data: %s", json.dumps(limit_data))
                    response = requests.post(url, headers=headers, data=json.dumps(limit_data))
                    logging.warning("Check response.status_code: %s", response.status_code)
                    logging.warning("Check response.content: %s", response.content)
                    if response.status_code not in [200, 201]:
                        raise except_orm(_('Error'), _("Error in syncing response for product %s %s") % (data.product_id.name, response.content,))
            self.write(cr, uid, ids, {'is_sync_woo': True}, context=context)

product_limit()