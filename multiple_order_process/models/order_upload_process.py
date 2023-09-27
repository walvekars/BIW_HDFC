# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from pathlib import Path
import os, base64, tempfile, binascii, xlrd
import datetime
from odoo.exceptions import UserError, ValidationError

class company_sign(models.Model):
    _inherit = 'res.company'

    sign = fields.Binary()

class enhance_contacts(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(tracking=True)
    pan_no = fields.Char(string='Pan No')
    cin_no = fields.Char(string='CIN No')
    program_name = fields.Char(string='Program Name')
    program_code = fields.Char(string='Program Code')
    region = fields.Char(string='Region')
    attn_name = fields.Char(string='Attn name')
    street3 = fields.Char()
    ph_off = fields.Char(string='Office Phone')
    primary_contact = fields.Char(string='Primary Contact')  # doubt
    tries = fields.Many2one('multi.try', string='Tries', readonly=0, tracking=True, ondelete="restrict")
    unique_ref = fields.Many2one('pemt.rec', string='Unique Ref')  # doubt
    # order_no = fields.Char(realated='parent_id.name', string='Order No', store=True)  # doubt
    product_catalogue = fields.One2many('client.catalogue', 'client', string='Product Catalogue', readonly=True)
    property_product_pricelist = fields.Many2one(
        'product.pricelist', 'Pricelist', compute='_compute_product_pricelist', store=True,
        inverse="_inverse_product_pricelist", company_dependent=False,
        domain=lambda self: [('company_id', 'in', (self.env.company.id, False))],
        help="This pricelist will be used, instead of the default one, for sales to the current partner")

class TemporaryRecords(models.Model):
    _name = 'temp.rec'
    _rec_name = 'unique_ref'
    _description = 'Order Upload'

    unique_ref = fields.Char(string='UNIQUE REF', required=True, readonly=True, default=lambda self: _('New'))
    file_name = fields.Many2one('store.files', string='FILE NAME')
    up_date = fields.Datetime(string='FILE UPLOAD DATE-TIME')
    customer = fields.Many2one('res.partner', string='CUSTOMER')

    validated = fields.Boolean(default=False)

    ref_no = fields.Char(string='REFERENCE NO', store=True)
    customer_name = fields.Char(string='NAME')
    add1 = fields.Char(string='ADD1')
    add2 = fields.Char(string='ADD2')
    add3 = fields.Char(string='ADD3')
    city = fields.Char(string='CITY')
    zip_code = fields.Char(string='ZIP CODE')
    ph_res = fields.Char(string='PH RES')
    ph_off = fields.Char(string='PH OFF')
    mobile = fields.Char(string='MOBILE')
    email_id = fields.Char(string='EMAIL ID')
    item_code = fields.Char(string='ITEM CODE')
    item_desc = fields.Char(string='ITEM DESCRIPTION')
    global_item_code = fields.Many2one('product.template', string='GLOBAL ITEM CODE & DESCRIPTION', ondelete='restrict')
    qty = fields.Integer(string='QTY')

    @api.model
    def create(self, vals):
        if vals.get('unique_ref', _('New')) == _('New'):
            vals['unique_ref'] = self.env['ir.sequence'].next_by_code(
                'temp.rec') or _('New')
        res = super(TemporaryRecords, self).create(vals)
        return res

    def validate(self):
        return self.env.ref('multiple_order_process.validation_report').report_action(self)

    def process_to_master(self, wiz):
        # selected ids in list
        selected_ids = self.env.context.get('active_ids', [])

        # converting selected ids to record tuple
        selected_records = self.browse(selected_ids)

        res_partners = self.env['res.partner'].search([])
        product_template = self.env['product.template'].search([])

        vals = []
        delete = []
        all_pemt_ids = []
        # fetching selected values of list
        for ids in selected_records:

            if ids.validated == False:
                raise ValidationError(
                    'Please click on "VALIDATE" and download validated file once (for future reference) and Proceed')

            else:
                order = self.env['pemt.rec'].create({
                    # 'try_no': self.env['multi.try'].search([('type', '=', '0')]).id,
                    'unique_ref': ids.unique_ref,
                    'file_name': ids.file_name.id,
                    'up_date': ids.up_date,
                    'ref_no': ids.ref_no,
                    'item_code': ids.item_code,
                    'global_item_code': ids.global_item_code.id,
                    'item_desc': ids.item_desc,
                    'qty': ids.qty,
                })

                contact = res_partners.create({
                    'unique_ref': order.id,
                    'parent_id': wiz.select_customer.id,
                    'type': 'delivery',
                    'company_type': 'person',
                    'name': ids.customer_name,
                    'street': ids.add1,
                    'street2': ids.add2,
                    'street3': ids.add3,
                    'city': ids.city,
                    'zip': ids.zip_code,
                    'mobile': ids.mobile,
                    'ph_off': ids.ph_off,
                    'phone': ids.ph_res,
                    'email': ids.email_id,
                    'tries': self.env['multi.try'].search([('type', '=', '0')]).id
                })

                order.update({
                    'customer_name': contact.id
                })

                all_pemt_ids.append(order)

                vals.append((0, 0, {
                    'product_id': ids.global_item_code.id,
                    'name': ids.item_desc,
                    'contact_name': contact.id,
                    'product_uom_qty': ids.qty
                }))
                delete.append(ids.id)

        new_sale_order = wiz.env['sale.order'].create({
            'state': 'draft',
            'partner_id': wiz.select_customer.id,
            'order_line': vals
        })

        for recs in all_pemt_ids:
            recs.order_no = new_sale_order.id

        self.env['temp.rec'].search([('id', 'in', delete)]).unlink()

    def automated_process(self, vals):
        path = Path(self.env['config.scheduled.sftp'].search([('id', '=', vals)]).name.path)
        company = (self.env['config.scheduled.sftp'].search([('id', '=', vals)]).name.company)
        for all_files in os.listdir(path):

            file_path = os.path.join(path, all_files)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as file:
                    file_data = base64.b64encode(file.read())

            try:
                file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                print(file)
                file.write(binascii.a2b_base64(file_data))
                file.seek(0)
                workbook = xlrd.open_workbook(file.name)
                sheet = workbook.sheet_by_index(0)
                print(sheet)
            except:
                raise UserError(_("Invalid file! (Allowed format - .xlsx)"))

            exist_file = self.sudo().env['store.files'].search([('extension_name', '=', all_files)])
            if exist_file:
                raise ValidationError(_('file Already Uploaded'))
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
                            if company == recs.client:
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

                file_name_without_extension = os.path.splitext(all_files)[0]
                new_file_stored = self.sudo().env['store.files'].create({
                    'data': file_data,
                    'name': file_name_without_extension,
                    'extension_name': all_files,
                    'upload_time': datetime.datetime.now(),
                    'client_id': company.id,
                })

                master_sheet_new = []
                product_line = []
                for row_no in range(sheet.nrows):
                    line = list(map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if row_no > 0:
                        print(line[0])
                        for prods in client_code_id:
                            if line[11].strip() == prods.client_code.strip():
                                master_id = self.env['pemt.rec'].create({
                                    'ref_no': line[0].strip(),
                                    'file_name': new_file_stored.id,
                                    'up_date': new_file_stored.upload_time,
                                    'item_code': line[11].strip(),
                                    'item_desc': line[12].strip(),
                                    'qty': line[13].strip(),
                                    'global_item_code': prods.global_code.id,
                                })

                                master_sheet_new.append(master_id)
                                contact = self.env['res.partner'].create({
                                    'unique_ref': master_id.id,
                                    'parent_id': company.id,
                                    'type': 'delivery',
                                    'company_type': 'person',
                                    'name': line[1].strip(),
                                    'street': line[2].strip(),
                                    'street2': line[3].strip(),
                                    'street3': line[4].strip(),
                                    'city': line[5].strip(),
                                    'zip': line[6].strip(),
                                    'mobile': line[9].strip(),
                                    'ph_off': line[8].strip(),
                                    'phone': line[7].strip(),
                                    'email': line[10].strip(),
                                    'tries': self.env['multi.try'].search([('type', '=', '0')]).id
                                })

                                master_id.update({
                                    'customer_name': contact.id
                                })

                                product_line.append((0, 0, {
                                    'product_id': master_id.global_item_code.id,
                                    'name': master_id.item_desc,
                                    'contact_name': contact.id,
                                    'product_uom_qty': master_id.qty
                                }))

                new_sale_order = self.env['sale.order'].create({
                    'state': 'draft',
                    'partner_id': company.id,
                    'order_line': product_line
                })

                for new_orders in master_sheet_new:
                    new_orders.order_no = new_sale_order.id

                new_file_stored.update({
                    'order_count': len(master_sheet_new)
                })

class StoreFiles(models.Model):
    _name = 'store.files'

    name = fields.Char(string='File Name')
    extension_name = fields.Char(string='File Name With Extension')
    data = fields.Binary(string='File Data')
    upload_time = fields.Datetime(string="Upload Time")
    client_id = fields.Many2one('res.partner', ondelete='restrict', string='Client')
    order_count = fields.Integer(string='No. Of Orders')

    @api.constrains('name')
    def process_new_order(self):
        print("new order")

class ProductTemplateEnhance(models.Model):
    _inherit = 'product.template'

    mrp_field = fields.Float()
    com_measurement = fields.Char(string="Measurement (L*B*H) in cms", compute='_compute_com_measurement')
    measurement = fields.Float(string="Length")
    breadth = fields.Float()
    height = fields.Float()
    product_weight = fields.Float(string="Product Weight in Kg")
    product_volumetric_weight = fields.Float(string="Product Volumetric Weight in kg")
    packing_material = fields.Char(string="Packing Material – Box Type/Cover code")
    country_of_origin = fields.Char(string="Country Of Origin")
    detailed_type = fields.Selection(selection_add=[
        ('product', 'Storable Product')
    ], tracking=True, default='product', readonly=1, ondelete={'product': 'set consu'})
    client_catalogue = fields.One2many('client.catalogue', 'global_code', string='Client Catalogue', readonly=True)
    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price', store=True,
        digits='Product Price', groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
        In FIFO: value of the next unit that will leave the stock (automatically computed).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""")


    def _compute_com_measurement(self):
        for rec in self:
            measurement = str(rec.measurement) + '*' + str(rec.breadth) + '*' + str(rec.height)
            rec.com_measurement = measurement

''' in sftp configuration need to include
1. company_id i.e customer
2. 

'''