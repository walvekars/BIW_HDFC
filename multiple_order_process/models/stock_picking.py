# -*- coding: utf-8 -*-
import datetime

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockPickingEnhanced(models.Model):
    _inherit = 'stock.picking'

    courier_company = fields.Many2one('courier.company.code', string='Courier Company', readonly=0, ondelete='restrict')
    awb_number = fields.Many2one('air.way.bill', string='AWB Number', readonly=0, ondelete='restrict')
    hand_off_id = fields.Char(string='Hand-off ID', readonly=1)
    invoiced_id = fields.Many2one('account.move', string='Invoiced ID', readonly=1)
    hand_off_date_time = fields.Datetime(readonly=1)
    order_status = fields.Selection([
        ('wip', 'WIP'),
        ('ready', 'READY'),
        ('hand_off', 'HAND_OFF'),
        ('not_serviceable', 'NOT_SERVICEABLE'),
        ('cancelled', 'CANCELLED'),
        ('dispatched', 'DISPATCHED'),
        ('delivered', 'DELIVERED'),
        ('returned', 'RETURNED'),
        ('re_dispatched', 'RE_DISPATCHED')], tracking=True, readonly=1)
    zip = fields.Char(related='partner_id.zip', store=True)
    unique_ref = fields.Many2one('pemt.rec', string='Unique Reference', related='partner_id.unique_ref', readonly=1, store=True)
    hub = fields.Char(string='HUB', related='courier_company.hub', readonly=1, store=True)
    airport = fields.Char(string='Airport', related='courier_company.airport', readonly=1, store=True)
    invoice_date = fields.Date(string='Invoice Date', related='invoiced_id.invoice_date', readonly=1, store=True)
    credit_note_number = fields.Many2one('account.move', string='Credit Note Number', readonly=1)
    credit_note_date = fields.Date(string='Credit Note Date', related='credit_note_number.invoice_date', readonly=1, store=True)
    return_order = fields.Many2one('stock.picking', string='Return Order', readonly=1)

    @api.constrains('partner_id')
    def created_do_order(self):
        for rec in self:
            if rec.picking_type_code == 'outgoing':
                rec.partner_id.unique_ref.delivery_id = rec.id

    @api.constrains('state')
    def order_status_sync(self):
        for rec in self:
            if rec.picking_type_code == 'outgoing':
                if rec.state == 'draft':
                    rec.order_status = 'wip'
                if rec.state == 'waiting':
                    rec.order_status = 'wip'
                    # rec.partner_id.unique_ref.wip_date = datetime.datetime.now()
                if rec.state == 'confirmed':
                    rec.order_status = 'wip'
                if rec.state == 'assigned':
                    rec.order_status = 'ready'
                if rec.state == 'done':
                    rec.order_status = 'dispatched'
                if rec.state == 'cancel':
                    rec.order_status = 'cancelled'


    def confirm_hand_off(self):
        courier_priority = self.env['courier.priority'].search([])
        tot_couriers = {}
        for couriers in courier_priority:
            tot_couriers[couriers.priority_no] = couriers.courier_company
        sorted = list(set(tot_couriers))
        if len(list(tot_couriers)) == 0:
            raise UserError('There are no courier companies available')

        for rec in self:
            if rec.picking_type_code == 'outgoing':
                if rec.state == 'assigned' and rec.order_status == 'ready':
                    if rec.zip != '':
                        for courier in range(len(sorted)):
                            if rec.courier_company.id == False and rec.awb_number.id == False:
                                parent_pincode_ids = tot_couriers[sorted[courier]].courier_pincode_ids.search([('pin_code', '=', rec.zip)])
                                pincode_id = tot_couriers[sorted[courier]].courier_pincode_ids.search([('courier_company', '=', tot_couriers[sorted[courier]].id), ('pin_code', '=', rec.zip)])
                                awb_remaining = pincode_id.courier_company.serviced_awb.search([('delivery_order_number', '=', False), ('serviced_awb_link', '=', pincode_id.courier_company.id)])
                                if parent_pincode_ids:
                                    if pincode_id:
                                        if len(awb_remaining) != 0:
                                            rec.courier_company = pincode_id.id
                                            rec.awb_number = awb_remaining[0].id
                                            awb_remaining[0].delivery_order_number = rec.id
                                            rec.order_status = 'hand_off'
                                        else:
                                            raise UserError("Shortage of AWB No(s) to assign")
                                else:
                                    rec.order_status = 'not_serviceable'
                    else:
                        rec.order_status = 'not_serviceable'
                else:
                    raise UserError('Order(s) is/are not in Ready state to Hand-off')
            else:
                raise UserError('Please Select Delivery Orders Only')

        # not_awb_list = []
        # for not_awb in self:
        #     if not_awb.order_status == 'ready':
        #         not_awb_list.append(not_awb)
        # if len(not_awb_list) > 0:
        #     raise UserError("Shortage of " + str(len(not_awb_list)) + " AWB No(s) to assign")

        cour_company_list = []
        for recs in self:
            if recs.courier_company:
                cour_company_list.append(recs.courier_company.courier_company)
        print(cour_company_list)

        map_hand_off_id = {}
        for cour in set(cour_company_list):
            map_hand_off_id[cour] = self.env['ir.sequence'].next_by_code('hand_off_ids')
        print(map_hand_off_id)

        for lines in self:
            for ids in map_hand_off_id:
                if lines.courier_company.courier_company == ids:
                    lines.hand_off_id = map_hand_off_id[ids]
                    lines.hand_off_date_time = datetime.datetime.now()

    def button_validate(self):
        for recs in self:
            if recs.picking_type_code == 'outgoing' and 'Return of ' not in recs.origin:
                if recs.order_status == 'hand_off':
                    res = super(StockPickingEnhanced, self).button_validate()
                else:
                    raise UserError('Order(s) is/are not yet handed to Courier Company')
                return res
            else:
                return super(StockPickingEnhanced, self).button_validate()



    # Every redispatch must have unique records in res.partners
    # send unique reference again to res.partners to use in stock.picking
