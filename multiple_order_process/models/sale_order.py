# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from num2words import num2words
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