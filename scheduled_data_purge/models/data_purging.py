# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api, _
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

    def data_purge(self, val):
        print("data purging.............")
        logger.info(f'Data Purging....')
        schedule_data_purging = self.search([('id', '=', val)])
        logger.info(f"{schedule_data_purging} Data Purging Record")
        print(schedule_data_purging)
        days_before = schedule_data_purging.days_before
        print(days_before)
        logger.info(f"Days Before: {days_before}")
        that_date = datetime.date.today() - datetime.timedelta(days=days_before)
        print(that_date)
        logger.info(f"That date: {that_date}")
        company_id = schedule_data_purging.name
        print(company_id)
        logger.info(f"Company ID: {company_id}")
        print(that_date.strftime('%d-%m-%Y'))
        logger.info(f'Without conversion: {that_date}')
        logger.info(f"With conversion: {that_date.strftime('%Y-%m-%d')}")
        print(self.env['pemt.rec'].search([]).customer)
        logger.info(self.env['pemt.rec'].search([]).customer)
        # logger.info(f"Update dates got in master 'DD:MM:YYYY': {self.env['pemt.rec'].search([('up_date', '=', that_date.strftime('%d-%m-%Y'))])}")
        # logger.info(f"Update dates got in master 'MM:DD:YYYY': {self.env['pemt.rec'].search([('up_date', '=', that_date.strftime('%m-%d-%Y'))])}")
        logger.info(f"Update dates got in master 'YYYY:MM:DD': {self.env['pemt.rec'].search([('up_date', '=', that_date.strftime('%Y-%m-%d'))])}")
        logger.info(f"customer got in master: {self.env['pemt.rec'].search([('customer', '=', company_id.name)])}")
        up_date_recs = self.env['pemt.rec'].search([('up_date', '=', that_date.strftime('%Y-%m-%d')), ('customer', '=', company_id.name)])
        print(up_date_recs)
        logger.info(f"Updating Records in master sheet: {up_date_recs}")
        print(len(up_date_recs))
        logger.info(f"Total Updating records in master: {len(up_date_recs)}")
        up_date_recs.update(
            {
                'field12': False,
                'field14': False,
                'field15': False,
                'field16': False,
                'field17': False,
                'field18': False,
                'add3_997': False,
                'field19': False,
                'field20': False,
                'field21': False,
                'field22': False,
                'field23': False,
                'field24': False,
                'field26': False,
                'field27': False,
                'field28': False,
                'field29': False,
                'field30': False,
                'add3_996': False,
                'field31': False,
                'field32': False,
                'field33': False,
                'field34': False,
                'field35': False,
                'field36': False,
                'field40': False,
            }
        )

        print("cammmmmmmmmmmmmmmmmmm")
        logger.info(f"after master")

        up_date_list = []
        for recs in up_date_recs:
            up_date_list.append(recs.unique_ref)

        print("jjjjjjjjjjjjj")
        logger.info(f"update list for Contacts: {up_date_list}")

        res_partner = self.env['res.partner'].search([('unique_ref', 'in', up_date_list)])
        logger.info(f"Contacts list: {res_partner}")
        for to_purge in res_partner:
            to_purge.update(
                {
                    'name': to_purge.unique_ref,
                    'street': False,
                    'street2': False,
                    'city': False,
                    'state_id': False,
                    'zip': False,
                    'mobile': False,
                    'email': False,
                }
            )

        # stock_picking = self.env['stock.picking'].search([('unique_ref', 'in', up_date_list)])
        # print(stock_picking)

class ColumnToPurge(models.Model):
    _name = 'column.to.purge'
    _description = 'Tables and Columns To Purge'

    name = fields.Many2one('ir.model')
    columns = fields.Many2many('ir.model.fields')
    data_purge_id = fields.Many2one('schedule.data.purging')