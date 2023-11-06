# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from num2words import num2words
import json
from odoo.exceptions import ValidationError, UserError
import datetime
class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    contact_name = fields.Many2one('res.partner', string="Contact Name")

    @api.onchange('product_id')
    def onchange_product_partner(self):
        if not self.contact_name:
            self.contact_name = self.order_id.partner_shipping_id

    def _prepare_procurement_values(self, group_id=False):
        res = super(sale_order_line, self)._prepare_procurement_values(group_id)
        if self.contact_name:
            a = res.update({'partner_id': self.contact_name.id or self.order_id.partner_shipping_id.id or False})
        return res


class stock_move(models.Model):
    _inherit = 'stock.move'

    def _key_assign_picking(self):
        keys = super(stock_move, self)._key_assign_picking()
        return keys + (self.partner_id,)

    def _search_picking_for_assignation(self):
        self.ensure_one()
        picking = super(stock_move, self)._search_picking_for_assignation()
        if self.sale_line_id and self.partner_id:
            picking = picking.filtered(lambda l: l.partner_id.id == self.partner_id.id)
            if picking:
                picking = picking[0]
        return picking

class PurchaseOrderNew(models.Model):
    _inherit = "purchase.order"

    def amount_to_text(self, total):
        amt_txt = num2words(total)
        amt_upp = amt_txt.upper()
        return amt_upp



########################## startts for multi invoice thing here     ############################



class compress_product_quantity(models.Model):
    _name = 'compress.product.quantity'

    customer_ref = fields.Char(string='Customer ID')
    delivery_ref = fields.Char(string='Delivery ID')
    at_status = fields.Char(string='Status')
    product_ref = fields.Many2one('sale.order')
    for_invoice = fields.Many2one('account.move')
    for_invoice_same = fields.Many2one('account.move')
    product_name = fields.Char()
    product_code = fields.Many2one('product.product', 'Product')
    compress_product_quantity = fields.Float()
    product_unit_price = fields.Float()
    tax = fields.Char()
    hsn = fields.Char()
    total = fields.Float()


class IndividualProductInvoice(models.Model):
    _inherit = 'account.move'

    compressed_invoice = fields.One2many('compress.product.quantity', 'for_invoice')
    compressed_invoice_change = fields.One2many('compress.product.quantity', 'for_invoice_same')
    reference_po_no = fields.Char(string='Reference/Po No')
    program = fields.Char(string='Program')
    po_no = fields.Char(string='PO No')
    attn = fields.Char(string='Attn', related='partner_id.attn_name')

    def name_get(self):
        res = []
        for invoice in self:
            if not self.env.context.get('invoice_with_status'):
                res.append(
                    (invoice.id, '%s %s' % (dict(invoice._fields['state'].selection).get(invoice.state), invoice.name)))
            else:
                res.append((invoice.id, '%s' % invoice.name))
        return res

    @api.constrains('l10n_in_gst_treatment')
    def on_invoiced(self):
        if self.move_type == 'out_invoice':
            for lines in self.compressed_invoice_change:
                stock_picking = self.env['stock.picking'].search([('name', '=', lines.delivery_ref)])
                for recs in stock_picking:
                    recs.invoiced_id = self
        if self.move_type == 'out_refund':
            for lines in self.compressed_invoice_change:
                stock_picking = self.env['stock.picking'].search([('unique_ref', '=', lines.customer_ref)])
                for recs in stock_picking:
                    recs.credit_note_number = self
        if self.pricelist_id:
            for line in self.compressed_invoice_change:
                for prod in self.pricelist_id.item_ids:
                    product_temp_id = self.env['product.template'].search([('id', '=', line.product_code.id)])
                    if prod.product_tmpl_id == product_temp_id:
                        total = prod.fixed_price * line.compress_product_quantity
                        line.update({'product_unit_price': prod.fixed_price, 'total': total})
