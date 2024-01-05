# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

logger = logging.getLogger(__name__)

class ConfigDataPurge(models.Model):
    _inherit = 'ir.cron'

    data_purge_details = fields.Many2one('schedule.data.purging', ondelete="cascade")

class ConfigDataPurging(models.Model):
    _name = 'schedule.data.purging'

    name = fields.Many2one('res.partner', string='Company', ondelete="restrict")
    days_before = fields.Integer(string='Days Before', required=True)
    execute_every = fields.Integer(string='Execute Every', required=True)
    interval_type = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], required=True)
    priority = fields.Integer(string='Priority', required=True)
    time_to_execute = fields.Datetime(string='Time', required=True)
    done_creation = fields.Boolean(default=False)
    ir_cron = fields.Many2one('ir.cron', ondelete="restrict")
    purge_ids = fields.One2many('column.to.purge', 'data_purge_id')

    _sql_constraints = [
        ('unique_priority', 'unique (priority)', 'Company and Priority should be unique'),
        ('unique_company', 'unique (name)', 'Company and Priority should be unique')
    ]

    @api.constrains('name')
    def schedule_purging(self):
        print(datetime.timedelta(days=1))
        new_create = self.env['ir.cron'].create(
            {
                'name': self.name.name + ' - Data Purge',
                'model_id': self.env['ir.model'].search([('model', '=', 'schedule.data.purging')]).id,
                'user_id': self.env.uid,
                'interval_number': self.execute_every,
                'interval_type': self.interval_type,
                'active': True,
                'nextcall': self.time_to_execute,
                'numbercall': -1,
                'priority': self.priority,
                'data_purge_details': self.id,
                'code': 'model.data_purge(' + str(self.id) + ')'
            }
        )
        print(new_create, self)
        self.ir_cron = new_create.id
        if self.done_creation != True:
            self.done_creation = True

    @api.onchange('time_to_execute')
    def _onchange_time_to_execute(self):
        self.ir_cron.nextcall = self.time_to_execute
        print(self.ir_cron)

    @api.onchange('execute_every')
    def _onchange_execute_every(self):
        self.ir_cron.interval_number = self.execute_every

    @api.onchange('interval_type')
    def _onchange_interval_type(self):
        self.ir_cron.interval_number = self.interval_type

    @api.constrains('purge_ids')
    def on_save_purge(self):
        if not self.purge_ids[-1].name.name == 'Contact':
            raise ValidationError("At Present Only Supports For - Contact Table")
        if len(set(self.purge_ids)) > 1:
            raise ValidationError("Repeating of same table is not allowed")

    def data_purge(self, val):
        schedule_data_purging = self.search([('id', '=', val)])
        days_before = schedule_data_purging.days_before
        that_date = datetime.datetime.now() - datetime.timedelta(days=days_before)
        company_id = schedule_data_purging.name
        up_date_recs = self.env['pemt.rec'].search([('up_date', '<=', that_date), ('customer_name.parent_id', '=', company_id.name), ('purged', '=', False)])
        # up_date_recs = self.env['pemt.rec'].search([('up_date', '>=', that_date), ('customer_name.parent_id', '=', company_id.name)])

        print(up_date_recs)


        logger.info(f'Data Purging....')
        logger.info(f"{schedule_data_purging} Data Purging Record")
        logger.info(f"Days Before: {days_before}")
        logger.info(f"That date: {that_date}")
        logger.info(f"Company ID: {company_id}")

        table_fields = {}
        for records in schedule_data_purging.purge_ids:
            if records.name.model == 'res.partner':
                table_fields[records.name.model] = {}
                for columns in records.columns:
                    table_fields[records.name.model][str(columns.name)] = False

        # for now only contact,
        # later if wanted mastersheet, delivery.order can be included if some other fields of perticular column need to be purged
        for to_purge in table_fields:
            if to_purge == 'res.partner':
                for recs in up_date_recs:
                    recs.customer_name.update(table_fields[to_purge])
                    recs.customer_name.name = recs.unique_ref
                    recs.purged = True  # Tata New

    # def table_data_purge(self):


class ColumnToPurge(models.Model):
    _name = 'column.to.purge'
    _description = 'Tables and Columns To Purge'

    name = fields.Many2one('ir.model')
    columns = fields.Many2many('ir.model.fields')
    data_purge_id = fields.Many2one('schedule.data.purging')