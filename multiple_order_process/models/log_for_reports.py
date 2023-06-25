from odoo import models, fields, api

class AirWayBill(models.Model):
    _name = 'logs.report'

    report_name = fields.Char(string="Report")
    model_name = fields.Many2one("ir.model")
    record_id = fields.Many2one('stock.picking', string="Record Id")
    printed_by = fields.Char(string="Printed By")
    date_time = fields.Datetime(string='Date')