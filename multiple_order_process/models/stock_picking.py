# -*- coding: utf-8 -*-
import datetime, cups
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from num2words import num2words

class StockPickingEnhanced(models.Model):
    _inherit = 'stock.picking'

    # To Remove
    courier_company = fields.Many2one('courier.company.code', string='Courier Company', readonly=0, ondelete='restrict')
    # To Remove
    courier_company_char = fields.Char(string='Courier Company', readonly=0)
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
    return_date = fields.Date(related="unique_ref.return_date",string="Return Date",readonly=1)
    cancel_date = fields.Date(related="unique_ref.cancel_date",string="cancel Date",readonly=1)
    hub = fields.Char(string='HUB', related='courier_company.hub', readonly=1, store=True)
    airport = fields.Char(string='Airport', related='courier_company.airport', readonly=1, store=True)
    invoice_date = fields.Date(string='Invoice Date', related='invoiced_id.invoice_date', readonly=1, store=True)
    credit_note_number = fields.Many2one('account.move', string='Credit Note Number', readonly=1)
    credit_note_date = fields.Date(string='Credit Note Date', related='credit_note_number.invoice_date', readonly=1, store=True)
    return_order = fields.Many2one('stock.picking', string='Return Order', readonly=1)

    def name_get(self):
        res = []
        for lines in self:
            if self.env.context.get('hand_off_id'):
                res.append((lines.id, '%s' % lines.hand_off_id))
            else:
                res.append((lines.id, '%s' % lines.name))
        return res

    def fields_view_get(self, view_id=None, view_type='form', toolbar=True, submenu=False):
        ref_id = self.env.ref('multiple_order_process.action_report_delivery_form_printer').id
        ref_id1 = self.env.ref('multiple_order_process.action_report_greetings_template_printer').id
        result = super(StockPickingEnhanced, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        if view_type == 'tree' and result.get('arch'):
            toolbar = result['toolbar']
            actions = toolbar['action']
            print_op = toolbar['print']

            for i in actions:
                if (i['id'] == ref_id1):
                    print_op.append(i)
                    toolbar['print'] = print_op
                    actions.remove(i)
                    toolbar['action'] = actions
                    result['toolbar'] = toolbar
            actions = toolbar['action']

            for i in actions:
                if (i['id'] == ref_id):
                    print_op.append(i)
                    toolbar['print'] = print_op
                    actions.remove(i)
                    toolbar['action'] = actions
                    result['toolbar'] = toolbar

        return result

    @api.constrains('partner_id')
    def created_do_order(self):
        for rec in self:
            if rec.picking_type_code == 'outgoing':
                rec.partner_id.unique_ref.delivery_id = rec.id

    @api.constrains('state', 'move_ids_without_package.forecast_availability')
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
                if rec.move_ids_without_package.forecast_availability == rec.move_ids_without_package.product_uom_qty:
                    if rec.state == 'assigned':  # Ready
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

    def delivery_form_log(self):
        a = self.env.user.name
        log_report = self.env['logs.report'].search([])
        log_report.create({
            'report_name': "Delivery form",
            'record_id': self.id,
            'model_name': self.env['ir.model']._get(self._name).id,
            'printed_by': a,
            'date_time': datetime.datetime.now()
        })

    def greeting_log(self):
        a = self.env.user.name
        log_report = self.env['logs.report'].search([])
        log_report.create({
            'report_name': "Greetings Template",
            'record_id': self.id,
            'model_name': self.env['ir.model']._get(self._name).id,
            'printed_by': a,
            'date_time': datetime.datetime.now()
        })

    def total(self):
        total = 0
        for rec in self:
            total = total + (rec.unique_ref.qty * rec.unique_ref.global_item_code.mrp_field)
            return total

    def amt_to_text(self, total):
        amt_txt = num2words(total)
        return amt_txt.title()

    def delivery_form_printing(self):
        active_ids = self.env.context.get('active_ids', {})

        file, file_type = self.env.ref('multiple_order_process.action_report_delivery_form')._render_qweb_pdf(res_ids=active_ids)

        conn = cups.Connection()
        f = open('Delivery Form.pdf', 'wb')
        f.write(file)
        f.close()
        printers = conn.getPrinters()
        for printer_name in printers:
            if printer_name:
                conn.printFile(printer_name, 'Delivery Form.pdf', '', {})

    def greetings_template_printing(self):
        active_ids = self.env.context.get('active_ids', {})

        file, file_type = self.env.ref('multiple_order_process.action_report_greetings_report')._render_qweb_pdf(res_ids=active_ids)
        conn = cups.Connection()
        f = open('Greetings.pdf', 'wb')
        f.write(file)
        f.close()
        printers = conn.getPrinters()
        for printer_name in printers:
            if printer_name:
                conn.printFile(printer_name, 'Greetings.pdf', '', {})

    # Every redispatch must have unique records in res.partners
    # send unique reference again to res.partners to use in stock.picking
