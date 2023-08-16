# -*- coding: utf-8 -*-
from odoo import api, models, fields, _

class company_sign(models.Model):
    _inherit = 'res.company'

    sign = fields.Binary()