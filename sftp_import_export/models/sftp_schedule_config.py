# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from pathlib import Path
import os
import tempfile
import binascii
import xlrd

from odoo.exceptions import UserError, ValidationError


class ConfigDataPurge(models.Model):
    _inherit = 'ir.cron'

    sftp_details = fields.Many2one('config.scheduled.sftp', ondelete="cascade")

class ConfigSheduledSFTP(models.Model):
    _name = 'config.scheduled.sftp'
    _description = 'Configure Automated SFTP'

    name = fields.Many2one('config.sftp', string='Company ( SFTP )', required=True, ondelete="restrict")
    execute_every = fields.Integer(string='Execute Every', required=True)
    interval_type = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months')
    ], required=True)
    priority = fields.Integer(string='Priority', required=True)
    time_to_execute = fields.Datetime(string='Time', required=True)
    done_creation = fields.Boolean(default=False)
    ir_cron = fields.Many2one('ir.cron', ondelete="restrict")

    _sql_constraints = [
        ('unique_priority', 'unique (priority)', 'Company and Priority should be unique'),
        ('unique_company', 'unique (name)', 'Company and Priority should be unique')
    ]

    @api.constrains('name')
    def schedule_purging(self):
        new_create = self.env['ir.cron'].create(
            {
                'name': str(self.name.company.name) + ' - SFTP',
                'model_id': self.env['ir.model'].search([('model', '=', 'config.scheduled.sftp')]).id,
                'user_id': self.env.uid,
                'interval_number': self.execute_every,
                'interval_type': self.interval_type,
                'active': True,
                'nextcall': self.time_to_execute,
                'numbercall': -1,
                'priority': self.priority,
                'sftp_details': self.id,
                'code': 'model.process_order(' + str(self.id) + ')'
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
        self.ir_cron.interval_type = self.interval_type

    def process_order(self, vals):
        self.env['temp.rec'].automated_process(vals)

        # print("triggered.........", vals)
        # print(self.env['config.scheduled.sftp'].search([('id', '=', vals)]))
        # print(self.env['config.scheduled.sftp'].search([('id', '=', vals)]).name.path)
        # p = Path(self.env['config.scheduled.sftp'].search([('id', '=', vals)]).name.path)
        # print(p)
        # print(os.listdir(p))
        # print(Path(p).is_dir())
        #
        # for all_files in os.listdir(p):
        #     if all_files not in self.env['store.files'].sudo().search([]):
        #         print(all_files)
        #
        #         print(Path(p/all_files).is_file(), "2nd try")
        #
        #         file_open = open(Path(p/all_files), 'rb')
        #         print(file_open, "opened")
        #         print(type(file_open))
        #         file_data = file_open.read()
        #         # print(file_data, "data....")
        #         print(type(file_data))
        #
        #
        #         try:
        #             new_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        #             print(new_file)
        #             new_file.write(binascii.a2b_base64(file_data))
        #
        #             new_file.seek(0)
        #             values = {}
        #             workbook = xlrd.open_workbook(new_file.name)
        #             print(workbook)
        #             sheet = workbook.sheet_by_index(0)
        #             print(sheet)
        #         except:
        #             raise UserError(_("Invalid file! (Allowed format - .txt)"))
        #         #
        #         # exist_file = self.env['stored.file'].search([('file_name', '=', self.file_name)])
        #         # if exist_file:
        #         #     raise ValidationError(_('Chosen file Already Uploaded'))
        #         #
        #         # else:
        # # for files in p:
        # #     print(files)
