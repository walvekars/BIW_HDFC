from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import requests
import json
import logging
import re

_logger = logging.getLogger('E-Invoicing')


class EInvoicing(models.Model):
    _name = 'einvoicing.configuration'
    _rec_name = 'testing'

    testing = fields.Selection([('t', 'Testing'), ('p', 'Production')], string="Url Type")
    base_url = fields.Char('Url')
    active = fields.Boolean("Active", default=True)
    active_production = fields.Boolean("Production?", default=False)
    asp_id = fields.Char(string='ASP-ID')
    asp_password = fields.Char(string='ASP Password')
    eway_url_staging = fields.Char("Eway URL(Staging)", tracking=2,
                                   default='http://gstsandbox.charteredinfo.com/eicore/dec/v1.03/Invoice?aspid=')
    # ewaydetails_url = fields.Char("Eway URL(Staging)", tracking=2,
                                   # default='https://gstsandbox.charteredinfo.com/ewaybillapi/dec/v1.03/ewayapi')
    print_url_live = fields.Char("Eway Print URL(Live)", tracking=2,
                                help="Eway Print URL", default='https://einvapi.charteredinfo.com/aspapi/v1.0/')
    def handle_einvoicing_auth_token(self):
        warehouse = self.env['stock.warehouse'].search([('company_id','=',self.env.company.id)], limit=1)
        if not self.testing:
            raise UserError(_('Please Select Url Type'))
        if not self.asp_id:
            raise UserError(_('Please Enter ASP-ID'))
        if not self.asp_password:
            raise UserError(_('Please Enter ASP Password'))
        if not warehouse.gst_no:
            raise UserError(_('Please Enter Registered GSTIN'))
        if not warehouse.user_name:
            raise UserError(_('Please Enter Registered User Name'))
        if not warehouse.user_password:
            raise UserError(_('Please Enter User Password'))
        aspid = self.asp_id
        asppass = self.asp_password
        if self.testing == 't':
            url = 'http://gstsandbox.charteredinfo.com/eivital/dec/v1.04/auth?&aspid=' + aspid + '&password=' + asppass + '&Gstin=' + warehouse.gst_no + '&user_name=' + warehouse.user_name + '&eInvPwd=' + warehouse.user_password
        if self.testing == 'p':
            url = 'https://einvapi.charteredinfo.com/eivital/dec/v1.04/auth?&aspid=' + aspid + '&password=' + asppass + '&Gstin=' + warehouse.gst_no + '&user_name=' + warehouse.user_name + '&eInvPwd=' + warehouse.user_password
        response = requests.get(url)
        res = response.content
        res_dict = json.loads(res.decode('utf-8'))
        auth_token = res_dict['Data'].get('AuthToken')
        token_epiry = res_dict['Data'].get('TokenExpiry')
        dt = str(token_epiry)
        res1 = dt.replace('T', ' ')
        time = datetime.strptime(res1, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
        time1 = datetime.strptime(time, '%d/%m/%Y %H:%M:%S')

        warehouse.write({
            'auth_token': auth_token,
            'expire_date': time1  # datetime.now()
        })
        return True

class CountryState(models.Model):
    _inherit = 'res.country.state'
    _order = 'code'

    stcd = fields.Char("Stcd")


    


