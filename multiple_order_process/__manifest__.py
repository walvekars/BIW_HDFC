# -*- coding: utf-8 -*-
{
    'name': 'Multiple Order Processing - Automated',
    'author': 'Suprit S',
    'version': '1.0',
    'summary': "Automated records importing from order files uploaded in SFTP and creating sale order",
    'sequence': -10,
    'description': """Records importing from excel sheet sent by client for creating sale order""",
    'category': 'Services/services',
    'website': '',
    'depends': ['base', 'sale', 'account_invoice_pricelist', 'gts_einvoicing_withewaybill', 'report_xlsx', 'stock', 'sale_management', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/configuration.xml',
        'views/courier.xml',
        'views/order_upload_process.xml',
        'views/master_sheet.xml',
        'views/log_for_reports.xml',
        'views/update_master.xml',
        'views/re_dispatch.xml',
        'views/validation_report.xml',
        'views/stock_picking.xml',
        'views/sale_order.xml',
        'reports/shipment_file.xml',
        'reports/delivery_form.xml',
        'reports/greetings.xml',
        'reports/transit_invoice.xml',
        'reports/courier_hand_off.xml',
        'reports/hand_off_picklist.xml',
        # 'views/account_move.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}