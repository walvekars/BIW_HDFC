import json
import requests
import datetime
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class EbillCancel(models.TransientModel):
    _name = 'einvoice.cancel'

    cancel_reason = fields.Selection(
        [('1', 'Duplicate'), ('2', 'Data Entry Mistake'), ('3', 'Order Cancelled'), ('4', 'Others')],
        string='Cancel Reason')
    desc = fields.Text('Description')

    def cancel_einvoicing(self):
        active_id = self.env.context.get('active_id')

        order = self.env['account.move'].browse(active_id)
        date1 = datetime.strptime(str(order.invoice_date), '%Y-%m-%d').strftime('%d/%m/%Y')
        einvoicing = self.env['einvoicing.configuration'].search([])
        delivery = self.env['stock.picking'].search([('origin', '=', order.invoice_origin)], limit=1)
        if delivery:
            warehouse = delivery.picking_type_id.warehouse_id
        else:
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', order.company_id.id)], limit=1)
        data = einvoicing.handle_einvoicing_auth_token()

        if not order.irn_no:
            raise UserError(_('Please Create E-Invoice First'))
        if not einvoicing:
            raise UserError(_('No Configurations details found in the system for E-Invoicing.'))
        if not warehouse.auth_token:
            raise UserError(_('Please Check Auth Token in warehouse configuration is Expired or Null.'))
        if not einvoicing.testing:
            raise UserError(_('Please Set Url Type in E-Invoicing Configuration.'))
        if not einvoicing.asp_id:
            raise UserError(_('Please Enter ASP-ID in E-Invoicing Configurations.'))
        if not einvoicing.asp_password:
            raise UserError(_('Please Enter ASP Password in E-Invoicing Configurations.'))
        if not warehouse.gst_no:
            raise UserError(_('Please Enter Registered GSTIN in warehouse Configurations.'))
        if not warehouse.user_password:
            raise UserError(_('Please Enter User Password in warehouse Configurations.'))
        if not warehouse.user_name:
            raise UserError(_('Please Enter User Name in Warehouse Configurations.'))
        data = {
            "Irn": order.irn_no,
            "CnlRsn": self.cancel_reason,
            "CnlRem": self.desc
        }

        if einvoicing.testing == 't':
            url = 'https://gstsandbox.charteredinfo.com/eicore/dec/v1.03/Invoice/Cancel?aspid=' + einvoicing.asp_id + '&password=' + einvoicing.asp_password + '&Gstin=' + warehouse.gst_no + '&eInvPwd=' + warehouse.user_password + '&AuthToken=' + warehouse.auth_token + '&user_name=' + warehouse.user_name
            url = str(url)
        if einvoicing.testing == 'p':
            url = 'https://einvapi.charteredinfo.com/eicore/dec/v1.03/Invoice/Cancel?aspid=' + einvoicing.asp_id + '&password=' + einvoicing.asp_password + '&Gstin=' + warehouse.gst_no + '&eInvPwd=' + warehouse.user_password + '&AuthToken=' + warehouse.auth_token + '&user_name=' + warehouse.user_name
            url = str(url)
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        res = response.content
        res_dict = json.loads(res.decode('utf-8'))
        if res_dict.get('Status') == '1':
            a = res_dict['Data']
            n = json.loads(a)
            dt = n['CancelDate']
            order.write({'irn_cancel_date': dt})
            order.write({'eway_bill_status': 'cancel'})
            # raise ValidationError('IRN Number Cancel Successfully !')
            # self.env.user.notify_info(message='IRN Number Cancel Successfully !')
            notify = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    # 'title': _('Import Message'),
                    'message': 'IRN Number Cancel Successfully !',
                    'sticky': True,
                }
            }
            return notify

        if res_dict.get('Status') == '0':
            raise UserError(_(res_dict.get('ErrorDetails')))