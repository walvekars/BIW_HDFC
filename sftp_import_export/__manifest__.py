# -*- coding: utf-8 -*-
{
    'name': 'Trigger SFTP',
    'author': 'Suprit S',
    'version': '1.0',
    'summary': "Automated SFTP File Push and Pull",
    'sequence': -10,
    'description': """Capturing order file from a particular company's server and processing through SFTP based on a scheduled actions""",
    'category': 'Services/services',
    'website': '',
    'depends': ['base', 'multiple_order_process'],
    'data': [
        'security/ir.model.access.csv',
        'views/sftp_conf.xml',
        'views/sftp_schedule_config.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}