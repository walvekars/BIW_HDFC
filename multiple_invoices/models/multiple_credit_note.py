from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError


class MultipleCreditNote(models.TransientModel):
    _name = 'multiple.credit.note'

    partner_id = fields.Many2one('res.partner', string='Partner', compute='compute_credit_note_wiz')
    invoice_date = fields.Date(string='Credit Date', default=datetime.date.today())
    journal_id = fields.Many2one('account.journal', string='Journal', compute='compute_credit_note_wiz')

    @api.depends('partner_id', 'journal_id')
    def compute_credit_note_wiz(self):
        self.journal_id = self.env['account.journal'].search([('name', '=', 'Tax Invoices')]).id
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['stock.picking'].browse(selected_ids)
        partner_id_list = []
        for ids in selected_records:
            if not ids.invoiced_id:
                raise ValidationError('Please Select Invoiced Orders')
            if not ids.order_status=='cancelled':
                raise ValidationError('Please Select  Cancelled Orders after Return')
            else:
                partner_id_list.append(ids.partner_id.parent_id)
        if len(set(partner_id_list)) == 1:
            print(partner_id_list)
            self.partner_id = list(set(partner_id_list))[0]

    def multiple_credit_note(self):
        print(">>>>>>>>>>>>>>")
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['stock.picking'].browse(selected_ids)
        for recs in selected_records:
            uncompressed = [(0, 0, {
                'customer_ref': recs.unique_ref.unique_ref,
                'delivery_ref': recs.name,
                'product_code': recs.move_ids_without_package.product_id.id,
                'at_status': recs.order_status,
                'compress_product_quantity': recs.move_ids_without_package.product_uom_qty,
                'product_unit_price': recs.move_ids_without_package.product_id.list_price,
                'tax': recs.move_ids_without_package.product_id.taxes_id.name,
                'total': recs.move_ids_without_package.product_uom_qty * recs.move_ids_without_package.product_id.list_price
            })]

            compressed = [(0, 0, {
                'product_code': recs.move_ids_without_package.product_id.id,
                'compress_product_quantity': recs.move_ids_without_package.product_uom_qty,
                'product_unit_price': recs.move_ids_without_package.product_id.list_price,
                'tax': recs.move_ids_without_package.product_id.taxes_id.name,
                'total': recs.move_ids_without_package.product_uom_qty * recs.move_ids_without_package.product_id.list_price
            })]

            invoice_lines = [(0, 0, {
                'product_id': recs.move_ids_without_package.product_id.id,
                'quantity': recs.move_ids_without_package.product_uom_qty,
                'product_uom_id': recs.move_ids_without_package.product_uom,
                'tax_ids': recs.move_ids_without_package.product_id.taxes_id.ids,
                # 'price_unit': recs.move_ids_without_package.product_id.list_price,
                # 'price_subtotal': recs.move_ids_without_package.product_uom_qty * recs.move_ids_without_package.product_id.list_price,
            })]

            account_move = self.env['account.move'].create({
                'move_type': 'out_refund',
                'pricelist_id': recs.partner_id.property_product_pricelist,
                'state': 'draft',
                'partner_id': recs.partner_id.id,
                'invoice_date': self.invoice_date,
                'l10n_in_gst_treatment': 'consumer',
                'journal_id': self.journal_id.id,
                'compressed_invoice_change': uncompressed,
                'compressed_invoice': compressed,
                'invoice_line_ids': invoice_lines
            })

            recs.credit_note_number = account_move.id
