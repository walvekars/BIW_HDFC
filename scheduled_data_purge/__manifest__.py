# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'author': 'Suprit S',
    'name': 'Scheduled Data Purge',
    'version': '1.0',
    'summary': 'Purge data by scheduling them',
    'sequence': -10,
    'description': """Records related to particular company are purged on a scheduled basis, with a mentioned date range""",
    'category': 'Services/services',
    'website': '',
    'depends': ['base', 'multiple_order_process'],
    'data': [
        'security/ir.model.access.csv',
        'views/data_purging.xml'
    ],
    'assets': {},
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}