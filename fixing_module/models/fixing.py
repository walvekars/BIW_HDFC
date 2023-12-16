# -*- coding: utf-8 -*-
from odoo import api, models, fields, _

class StockPickingFixing(models.Model):
    _inherit = 'stock.picking'

    def courier_id_to_char(self):
        print("printing................")
        for recs in self:
            if recs.courier_company.id:
                recs.courier_company_char = recs.courier_company.courier_company.name
