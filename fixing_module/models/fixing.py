# -*- coding: utf-8 -*-
from odoo import api, models, fields, _

class StockPickingFixing(models.Model):
    _inherit = 'stock.picking'

    def courier_id_to_char(self):
        for recs in self:
            if recs.courier_company.id:
                recs.courier_company_id = recs.courier_company.courier_company
                recs.hub = recs.courier_company.hub
                recs.airport = recs.courier_company.airport