# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class SelectCustomerWizard(models.TransientModel):
    _name = 'select.customer.wizard'

    select_customer = fields.Many2one('res.partner', string='Process Order For :', readonly=True, compute='compute_selected_customer')
    no_of_orders = fields.Integer(string='No of Orders :', readonly=True, compute='compute_selected_customer')

    @api.depends('select_customer', 'no_of_orders')
    def compute_selected_customer(self):
        selected_ids = self.env.context.get('active_ids', [])
        print(selected_ids)
        selected_records = self.env['temp.rec'].browse(selected_ids)
        customer = []
        for ids in selected_records:
            customer.append(ids.customer.id)
        if len(set(customer)) == 1:
            self.select_customer = list(set(customer))[0]
            self.no_of_orders = len(customer)
        else:
            raise ValidationError('Please Select Orders containing same "Customer"')

    def action_submit(self):
        print("printed and submitted")
        return self.env['temp.rec'].process_to_master(self)


# here wizard for selecting customer and proceding by clicking button which calls another function in multiple_order_process i.e submit button


# and then creating validate button only which again calls validate function in same multiple_order_process