from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import datetime
import re


class MultipleInvoice(models.Model):
    _inherit = 'stock.picking'


class TreeViewName(models.Model):
    _inherit = 'account.move'

    @api.depends('partner_id', 'invoice_source_email', 'partner_id.name')
    def _compute_invoice_partner_display_info(self):
        for move in self:
            vendor_display_name = move.partner_id.name
            if not vendor_display_name:
                if move.invoice_source_email:
                    vendor_display_name = _('@From: %(email)s', email=move.invoice_source_email)
                else:
                    vendor_display_name = _('#Created by: %s', move.sudo().create_uid.name or self.env.user.name)
            move.invoice_partner_display_name = vendor_display_name


class CustomerDeliveryAddress(models.Model):
    _inherit = 'res.partner'

    def _get_contact_name(self, partner, name):
        return name

class GenerateMultipleInvoice(models.TransientModel):
    _name = 'generate.multiple.invoice'

    partner_id = fields.Many2one('res.partner', string='Partner', compute='compute_wizard_fields')
    journal_id = fields.Many2one('account.journal', string='Journal', compute='compute_wizard_fields')
    invoice_date = fields.Date(string='Invoice Date', default=datetime.date.today())
    payment_terms = fields.Many2one('account.payment.term', string='Payment Term')

    @api.depends('journal_id')
    def compute_wizard_fields(self):
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['stock.picking'].browse(selected_ids)

        for ids in selected_records:
            if not ids.unique_ref.dispatched_on:
                raise ValidationError('Please select Orders which are dispatched')
            if ids.invoiced_id:
                raise ValidationError('Please select Order(s) which is/are yet to be Invoiced')
            if not ids.zip:
                raise ValidationError("Please select a delivery order which has a Pincode. Recommend to create invoice after Hand-off i.e deliverable orders")

        partner_id_list = []
        for picking in selected_records:
            if picking.partner_id.parent_id:
                partner_id_list.append(picking.partner_id.parent_id.id)
        if len(set(partner_id_list)) == 1:
            self.partner_id = list(set(partner_id_list))[0]
        else:
            raise ValidationError('Please Select "Delivery-Orders" containing same customer')
        self.journal_id = self.env['account.journal'].search([('name', '=', 'Tax Invoices')]).id

    def creating_multiple_invoices(self):
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['stock.picking'].browse(selected_ids)

        for recs in selected_records:
            tax_type = ''
            if int(recs.partner_id.zip) < 600001 or int(recs.partner_id.zip) > 669999:
                recs.partner_id.update({
                    'property_account_position_id': self.env['account.fiscal.position'].search([('name', '=', 'Inter State')]).id
                })
                # if there is more than one taxes_id in product.product then below code takes only first,
                # if no taxes_id in product.product then that particular delivery orders invoice will be without any taxes.
                if recs.move_line_ids_without_package.product_id.taxes_id.ids:
                    first_id = recs.move_line_ids_without_package.product_id.taxes_id[0]
                    split_list = first_id.name.split(' ')
                    percentage = [item for item in split_list if '%' in item]
                    num = percentage[0].split('%')[0].strip()
                    tax_type = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('name', 'ilike', 'IGST'), ('name', 'like', str(num))])
                else:
                    tax_type = False
            else:
                # if there is more than one taxes_id in product.product then below code takes only first,
                # if no taxes_id in product.product then that particular delivery orders invoice will be without any taxes.
                if recs.move_line_ids_without_package.product_id.taxes_id.ids:
                    first_id = recs.move_line_ids_without_package.product_id.taxes_id[0]
                    split_list = first_id.name.split(' ')
                    percentage = [item for item in split_list if '%' in item]
                    num = percentage[0].split('%')[0].strip()
                    tax_type = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('name', 'ilike', 'GST'), ('name', 'not like', 'IGST'), ('name', 'like', str(num))])
                else:
                    tax_type = False

            uncompressed = [(0, 0, {
                'customer_ref': recs.unique_ref.unique_ref,
                'delivery_ref': recs.name,
                'product_code': recs.move_ids_without_package.product_id.id,
                'at_status': recs.order_status,
                'compress_product_quantity': recs.move_ids_without_package.product_uom_qty,
                'product_unit_price': recs.move_ids_without_package.product_id.list_price,
                # 'tax': recs.move_ids_without_package.product_id.taxes_id.name,
                'tax': False if tax_type == False else tax_type.name,
                'total': recs.move_ids_without_package.product_uom_qty * recs.move_ids_without_package.product_id.list_price,
            })]

            compressed = [(0, 0, {
                'product_code': recs.move_ids_without_package.product_id.id,
                'compress_product_quantity': recs.move_ids_without_package.product_uom_qty,
                'product_unit_price': recs.move_ids_without_package.product_id.list_price,
                # 'tax': recs.move_ids_without_package.product_id.taxes_id.name,
                'tax': False if tax_type == False else tax_type.name,
                'total': recs.move_ids_without_package.product_uom_qty * recs.move_ids_without_package.product_id.list_price
            })]

            invoice_lines = [(0, 0, {
                'product_id': recs.move_ids_without_package.product_id.id,
                'quantity': recs.move_ids_without_package.product_uom_qty,
                'product_uom_id': recs.move_ids_without_package.product_uom,
                # 'tax_ids': recs.move_ids_without_package.product_id.taxes_id.ids,
                'tax_ids': False if tax_type == False else tax_type.ids,
                # 'price_unit': recs.move_ids_without_package.product_id.list_price,
                # 'price_subtotal': recs.move_ids_without_package.product_uom_qty * recs.move_ids_without_package.product_id.list_price,
            })]

            account_move = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'pricelist_id': recs.partner_id.property_product_pricelist,
                'state': 'draft',
                'partner_id': recs.partner_id.id,
                'invoice_payment_term_id': self.payment_terms,
                'invoice_date': self.invoice_date,
                'l10n_in_gst_treatment': 'consumer',
                'journal_id': self.journal_id.id,
                'compressed_invoice_change': uncompressed,
                'compressed_invoice': compressed,
                'invoice_line_ids': invoice_lines
            })

            recs.invoiced_id = account_move.id
