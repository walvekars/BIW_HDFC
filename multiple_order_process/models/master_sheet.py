# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _

class PermanentRecords(models.Model):
    _name = 'pemt.rec'
    _description = 'Master Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'unique_ref'

    unique_ref = fields.Char(string='UNIQUE REF', default=lambda self: _('New'))
    file_name = fields.Many2one('store.files', string='FILE NAME', ondelete='restrict',tracking=True)
    up_date = fields.Datetime(string='FILE UPLOAD DATE - TIME',tracking=True)
    # customer = fields.Many2one('res.partner', string="CUSTOMER", ondelete='restrict')
    ref_no = fields.Char(string='REFERENCE NO',tracking=True)
    customer_name = fields.Many2one('res.partner', string="CLIENT, CUSTOMER", ondelete='restrict', store=True,tracking=True)
    add1 = fields.Char(string='ADD1', related='customer_name.street', store=True)
    add2 = fields.Char(string='ADD2', related='customer_name.street2', store=True)
    add3 = fields.Char(string='ADD3', related='customer_name.street3', store=True)
    city = fields.Char(string='CITY', related='customer_name.city', store=True)
    zip_code = fields.Char(string='ZIP CODE', related='customer_name.zip', store=True)
    ph_res = fields.Char(string='PH RES', related='customer_name.phone', store=True)
    ph_off = fields.Char(string='PH OFF', related='customer_name.ph_off', store=True)
    mobile = fields.Char(string='MOBILE', related='customer_name.mobile', store=True)
    email_id = fields.Char(string='EMAIL ID', related='customer_name.email', store=True)
    item_code = fields.Char(string='ITEM CODE',tracking=True)
    item_desc = fields.Char(string='ITEM DESCRIPTION',tracking=True)
    global_item_code = fields.Many2one('product.template', string='GLOBAL ITEM CODE & DESCRIPTION', ondelete='restrict',tracking=True)
    qty = fields.Integer(string='QTY',tracking=True)
    order_no = fields.Many2one('sale.order', string='ORDER NO', ondelete='restrict',tracking=True)
    delivery_id = fields.Many2one('stock.picking', string='DELIVERY ID', ondelete='restrict',tracking=True)
    wip_date = fields.Date(string='WIP DATE', help='This date updates based on First WIP Boolean field, if it is false date updates here and sets tpo True',tracking=True)
    first_wip = fields.Boolean(string='First WIP', default=False, help="Called First wip because, There are many wip states Those are ODOO - Waiting and Confirmed, and BIW - Ready and Not Serviceable",tracking=True)
    shipment_file_done_wip = fields.Boolean(default=False, help="This is for report purpose - Shipment File, WIP orders will be printed only once, the same orders will print once the status gets changed")
    hand_off_id = fields.Char(string='HAND-OFF ID', related='delivery_id.hand_off_id', store=True)
    hand_off_date = fields.Date(string='HAND-OFF Date',tracking=True)
    awb_nos = fields.Many2one('air.way.bill', string='AWB NO', related='delivery_id.awb_number', store=True)
    dispatched_on = fields.Date(string='DISPATCHED ON',tracking=True)
    courier = fields.Many2one('courier.company.code', string='COURIER', related='delivery_id.courier_company', store=True)  # to be changed to many2one
    pod_date = fields.Date(string='POD DATE',tracking=True)
    up_pod_date = fields.Date(string='DELIVERY UPDATE',tracking=True)
    person_delv = fields.Char(string='PERSON DELV',tracking=True)
    return_date = fields.Date(string='RETURN DATE',tracking=True)
    up_return_date = fields.Date(string='RETURN UPDATE',tracking=True)
    return_reason = fields.Char(string='RETURN REASON',tracking=True)
    cancel_date = fields.Date(string='CANCEL DATE',tracking=True)
    cancel_reason = fields.Char(string='CANCEL REASON',tracking=True)
    order_status = fields.Selection([
        ('wip', 'WIP'),  # (draft, waiting_another_operation, Waiting - ODOO status)
        ('ready', 'READY'),
        ('hand_off', 'HAND_OFF'),
        ('not_serviceable', 'NOT_SERVICEABLE'),
        ('cancelled', 'CANCELLED'),
        ('dispatched', 'DISPATCHED'),
        ('delivered', 'DELIVERED'),
        ('returned', 'RETURNED'),
        ('re_dispatched', 'RE_DISPATCHED')], string='STATUS', tracking=True, related='delivery_id.order_status', store=True)

    re_dispatch_update = fields.Datetime(string='RE-DISPATCH UPDATE',tracking=True)
    try_lines = fields.One2many('pemt.rec', 'parent_line')
    parent_line = fields.Many2one('pemt.rec', ondelete='cascade')
    try_no = fields.Many2one('multi.try', ondelete='restrict', related='customer_name.tries', store=True)
    try_no_type = fields.Selection(related='try_no.type', string='Try No', store=True)
    
    @api.model
    def create(self, vals):
        if vals.get('unique_ref', _('New')) == _('New'):
            vals['unique_ref'] = self.env['ir.sequence'].next_by_code(
                'temp.rec') or _('New')
        res = super(PermanentRecords, self).create(vals)
        return res

    def name_get(self):
        result = []
        for record in self:
            if self.env.context.get('custom_name', False):
                result.append((record.id, "{}".format(record.unique_ref)))
            else:
                result.append((record.id, "{}".format(record.unique_ref + ', ' + record.ref_no)))
        return result

    @api.constrains('order_status')
    def change_state(self):
        for rec in self:
            if rec.order_status == 'wip' and rec.first_wip == False:
                rec.wip_date = datetime.date.today()
                rec.first_wip = True
            if rec.order_status == 'hand_off':
                rec.hand_off_date = datetime.date.today()
            if rec.order_status == 'dispatched':
                rec.dispatched_on = datetime.date.today()