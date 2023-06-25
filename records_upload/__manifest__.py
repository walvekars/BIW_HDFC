# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Excel Records Import and Process Manually',
    'version': '1.0',
    'summary': 'Records importing from excel sheet sent by client for creating sale order manually',
    'author': 'Suprit S',
    'sequence': -20,
    'description': """Records importing from excel sheet sent by client for creating sale order""",
    'category': 'Services/services',
    'website': '',
    'depends': ['multiple_order_process'],
    'data': [
        'security/ir.model.access.csv',
        'views/choose_file.xml',
        'views/select_customer.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            '/records_upload/static/src/xml/import_button.xml',
        ],
        'web.assets_backend': [
            '/records_upload/static/src/js/import_button.js'
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}