{
    "name": "Stock - Multiple invoices",
    "version": "15.0.1.0.1",
    "summary": "This module is for multiple invoices",
    "category": "Application",
    "author": "Prime Minds Consulting Private Limited",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        'security/ir.model.access.csv',
        'views/multiple_invoices.xml',
        'views/multiple_credit_notes.xml'
    ],
    "installable": True,
}
