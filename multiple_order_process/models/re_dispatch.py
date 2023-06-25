# -*- coding: utf-8 -*-
from odoo import api, models, fields, _

class MultiTry(models.Model):
    _name = 'multi.try'
    _description = 'Try Types'

    name = fields.Char()
    type = fields.Selection([
        ('0', 'Fresh'),
        ('1', '1st'),
        ('2', '2nd'),
        ('3', '3rd')], string='Type', required=True)

    _sql_constraints = [
        ('unique_name', 'unique (name)', 'Selected Type already created')
    ]

    @api.constrains('type')
    def create_name(self):
        self.name = dict(self._fields['type'].selection).get(self.type)