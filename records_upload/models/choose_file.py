# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError
import tempfile
import binascii
import xlrd

class ChooseFile(models.TransientModel):
    _name = 'choose.file'

    file_data = fields.Binary(string='Choose Excel File')
    file_name = fields.Char(string='File Name')
    up_date = fields.Datetime(string='Upload Time')
    client_id = fields.Many2one('res.partner', string='Customer')

    def action_submit_file(self):
        try:
            file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            print(file)
            file.write(binascii.a2b_base64(self.file_data))
            file.seek(0)
            workbook = xlrd.open_workbook(file.name)
            sheet = workbook.sheet_by_index(0)
        except:
            raise UserError(_("Invalid file! (Allowed format - .xlsx)"))

        exist_file = self.sudo().env['store.files'].search([('extension_name', '=', self.file_name)])
        if exist_file:
            raise ValidationError(_('Chosen file Already Uploaded'))

        else:

            pemt_rec = self.env['pemt.rec'].search([])
            list_order_no = []
            for recs in pemt_rec:
                list_order_no.append(recs.ref_no)

            temp_rec = self.env['temp.rec'].search([])
            list_order_no_trial_sheet = []
            for vals in temp_rec:
                list_order_no_trial_sheet.append(vals.ref_no)

            product_template = self.env['product.template'].search([])
            client_code = []
            client_code_id = []
            for prod in product_template:
                if prod.client_catalogue:
                    for recs in prod.client_catalogue:
                        if self.client_id == recs.client:
                            client_code.append(recs.client_code.strip())
                            client_code_id.append(recs)

            rows = []
            for row_no in range(sheet.nrows):
                if row_no == 0:
                    pass
                else:
                    rows.append(row_no)
                    line = list(
                        map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(
                            row.value),
                            sheet.row(row_no)))

                    if line[0].strip() == '':
                        raise ValidationError("Order Number is Empty")

                    if line[0].strip() in list_order_no or line[0].strip() in list_order_no_trial_sheet:
                        raise ValidationError("Order Number Already exist")

                    if line[11].strip():
                        if line[11].strip() in client_code:
                            if line[13].strip() == '' or line[13].strip() == 0.0 or line[13].strip() == 0:
                                raise ValidationError("Quantity cannot be less than or equal to 0")
                            else:
                                pass
                        else:
                            raise ValidationError("Some Products(Client Code) Doesn't exist in Product Master")
                    else:
                        raise ValidationError("Product(s) Code can't be empty")

            self.up_date = datetime.now()
            stored_file = self.sudo().env['store.files'].search([])
            stored_file_data = stored_file.create({
                'data': self.file_data,
                'name': self.file_name.strip('.xlsx'),
                'extension_name': self.file_name,
                'upload_time': self.up_date,
                'client_id': self.client_id.id,
            })

            line_import_count = []
            for row_no in range(sheet.nrows):
                line = list(map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                if row_no > 0:
                    print(line[0])
                    # if line[0] == '':
                    #     print(line[0], 'false')

                    for prod in client_code_id:
                        if line[11].strip() == prod.client_code.strip():
                            temp_rec.create({
                                'file_name': stored_file_data.id,
                                'up_date': self.up_date,
                                'customer': self.client_id.id,
                                'ref_no': line[0].strip(),
                                'customer_name': line[1].strip(),
                                'add1': line[2].strip(),
                                'add2': line[3].strip(),
                                'add3': line[4].strip(),
                                'city': line[5].strip(),
                                'zip_code': line[6].strip(),
                                'ph_res': line[7].strip(),
                                'ph_off': line[8].strip(),
                                'mobile': line[9].strip(),
                                'email_id': line[10].strip(),
                                'item_code': line[11].strip(),
                                'item_desc': line[12].strip(),
                                'global_item_code': prod.global_code.id,
                                'qty': line[13].strip(),
                            })

                            line_import_count.append(1)

            stored_file_data.update({
                'order_count': len(line_import_count)
            })

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    # 'title': _('Import Message'),
                    'message': str(len(line_import_count)) + ' ' + 'Records Imported Successfully',
                    'sticky': True,
                }
            }
            return notification