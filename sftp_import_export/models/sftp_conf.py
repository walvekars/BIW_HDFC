# -*- coding: utf-8 -*-
from odoo import models, fields, _
from cryptography.fernet import Fernet
from odoo.exceptions import UserError
from datetime import datetime
from pathlib import Path
import paramiko
import pysftp

import logging, os
_logger = logging.getLogger(__name__)

class ConfigSFTP(models.Model):
    _name = 'config.sftp'
    _description = 'Configure SFTP'
    _rec_name = 'company'

    FILE_SIZE = 1000

    hostname = fields.Char(string='IP Host')
    username = fields.Char(string='Username')
    port = fields.Integer(string='Port Number')
    key = fields.Char(string='KEY')
    company = fields.Many2one('res.partner', string='Company', required=True, ondelete='restrict')
    passphrase = fields.Char(string='Passphrase')
    password = fields.Char(string='Password')

    path = fields.Char(string='Path - for testing')

    _sql_constraints = [
        ('unique_company', 'unique (company)', 'Multiple SFTP credentials cannot be mapped to a single company, either CHANGE THE COMPANY or DELETE OLD RECORD')
    ]

    def sftp_transfer(self):
        sftp_model = self.env['sftp.model'].search([])
        sftp_model.ensure_one()

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=sftp_model.hostname, username=sftp_model.username, password=sftp_model.password, port=sftp_model.port)  # suprit-s, 127.0.1.1, Suprit-Ubuntu, 127.1, 127.0.1
        sftp_client = ssh.open_sftp()
        # sftp_client.put(sftp_model.from_path, sftp_model.to_path + '/records_upload/static/src/files/')
        # sftp_client.get(sftp_model.from_path, sftp_model.to_path + '/records_upload/static/src/files')

        inbound_files = sftp_client.listdir('../BI-Worldwide_SCM/records_upload/static/src/keys')
        server_files = os.listdir('../BI-Worldwide_SCM/records_upload/static/src/keys')

        for file in inbound_files:
            if file not in server_files:

                # ps.FileCipher()

                # print(sftp_model.from_path + file, sftp_model.to_path + 'records_upload/static/src/files/' + file)
                # sftp_client.get(sftp_model.from_path + file, sftp_model.to_path + 'records_upload/static/src/files/' + file)   # /home/suprith_21s/Documents/odoo-15.0/custom_addons/biw/

                # Important  --------------------------------------------------------

                f = Fernet(sftp_model.key)
                sftp_client.get(sftp_model.from_path + file, sftp_model.to_path + file)
                with open(sftp_model.to_path + file, 'rb') as original_file:
                    original = original_file.read()
                    decrypted = f.decrypt(original)

                with open(sftp_model.to_path + file, 'wb') as decrypted_file:
                    decrypted_file.write(decrypted)

                # Important  --------------------------------------------------------

                # sftp_client.get(sftp_model.from_path + str(f.encrypt(bytes(file))), sftp_model.to_path + file)  # /home/suprith_21s/Documents/odoo-15.0/custom_addons/biw
                # sftp_client.get(sftp_model.from_path + file, sftp_model.to_path + file)  # /home/suprith_21s/Documents/odoo-15.0/custom_addons/biw

            else:

                # Important  --------------------------------------------------------

                f = Fernet(sftp_model.key)
                # print(file + ', ' + Path(file).stem + ', ' + Path(file).stem + '(re-' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + ')' + file[-(len(file) - len(Path(file).stem)):])
                # print(sftp_model.from_path + file, sftp_model.to_path + Path(file).stem + '(re-' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + ')' + file[-(len(file) - len(Path(file).stem)):])
                renamed_file = Path(file).stem + '(re-' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + ')' + file[-(len(file) - len(Path(file).stem)):]

                sftp_client.get(sftp_model.from_path + file, sftp_model.to_path + renamed_file)
                # print(sftp_model.to_path + renamed_file)
                with open(sftp_model.to_path + renamed_file, 'rb') as original_file:
                    original = original_file.read()
                    decrypted = f.decrypt(original)

                with open(sftp_model.to_path + renamed_file, 'wb') as decrypted_file:
                    decrypted_file.write(decrypted)

                # Important  --------------------------------------------------------

        return

    def test_sftp_connection(self, context=None):
        sftp_model = self.env['config.sftp'].search([])
        sftp_model.ensure_one()

        # Check if there is a success or fail and write messages
        message_title = ""
        message_content = ""
        error = ""
        has_failed = False
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        # Connect with external server over SFTP, so we know sure that everything works.
        try:
            pmcpl = '/home/suprit-s/Documents/odoo-15.0/custom_addons/BI-Worldwide_SCM/records_upload/static/src/keys/identity.pem'
            biw = '../data/odoo/custom/BI - Worldwide_SCM/records_upload/static/src/keys/600101558_pvt.pem'

            if not sftp_model.password:
                sftp_client = pysftp.Connection(host=sftp_model.hostname, port=sftp_model.port, username=sftp_model.username)
            else:
                # sftp_client = pysftp.Connection(host=sftp_model.hostname, port=sftp_model.port, username=sftp_model.username, private_key=biw, private_key_pass=sftp_model.passphrase, cnopts=cnopts)
                sftp_client = pysftp.Connection(host=sftp_model.hostname, port=sftp_model.port, username=sftp_model.username, password=sftp_model.password)
                # sftp_client.execute(str(sftp_model.password))

            sftp_client.close()
            message_title = _("Connection Test Succeeded!\nEverything seems properly set up for SFTP Transfer!")
        except Exception as e:
            _logger.critical('There was a problem connecting to the remote ftp: %s', str(e))
            error += str(e)
            has_failed = True
            message_title = _("Connection Test Failed!")
            if sftp_model.hostname == False or len(sftp_model.hostname) < 8:
                message_content += "\nYour IP address seems to be too short.\n"
            message_content += _("Here is what we got instead:\n")
        # finally:
        #     if sftp_client:
        #         sftp_client.close()

        if has_failed:
            raise UserError(message_title + '\n' + message_content + "%s" % str(error))
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    # 'title': _(message_title),
                    'message': message_title + '\n\n' + message_content,
                    'sticky': True,
                }
            }