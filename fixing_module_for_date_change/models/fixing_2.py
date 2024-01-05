# -*- coding: utf-8 -*-
import datetime

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class MasterAndOtherDateFix(models.Model):
    _inherit = 'pemt.rec'

    # @api.multi
    def check_admin_user(self):
        flag = self.env['res.users'].has_group('base.group_system')
        if flag:
            self.date_change_to_previous()
        else:
            raise UserError('You are not allowed to use this action')

    def date_change_to_previous(self):
        for recs in self:
            print(recs)

            # Master Sheet - one Day Back, Date Change
            recs.create_date = recs.create_date - datetime.timedelta(days=1)
            recs.up_date = recs.up_date - datetime.timedelta(days=1)
            recs.wip_date = recs.wip_date - datetime.timedelta(days=1)
            if recs.hand_off_date:
                recs.hand_off_date = recs.hand_off_date - datetime.timedelta(days=1)
            if recs.dispatched_on:
                recs.dispatched_on = recs.dispatched_on - datetime.timedelta(days=1)

            # Sale Order - one Day Back, Date Change
            recs.order_no.create_date = recs.order_no.create_date - datetime.timedelta(days=1)
            recs.order_no.date_order = recs.order_no.date_order - datetime.timedelta(days=1)
            recs.order_no.effective_date = recs.order_no.effective_date - datetime.timedelta(days=1)
            recs.order_no.expected_date = recs.order_no.expected_date - datetime.timedelta(days=1)
            if recs.order_no.signed_on:
               recs.order_no.signed_on = recs.order_no.signed_on - datetime.timedelta(days=1)
            if recs.order_no.validity_date:
               recs.order_no.validity_date = recs.order_no.validity_date - datetime.timedelta(days=1)
            if recs.order_no.commitment_date:
               recs.order_no.commitment_date = recs.order_no.commitment_date - datetime.timedelta(days=1)

            # Inventory - one Day Back, Date Change
            recs.delivery_id.create_date = recs.delivery_id.create_date - datetime.timedelta(days=1)
            recs.delivery_id.date = recs.delivery_id.date - datetime.timedelta(days=1)
            recs.delivery_id.date_deadline = recs.delivery_id.date_deadline - datetime.timedelta(days=1)
            if recs.delivery_id.hand_off_date_time:
                recs.delivery_id.hand_off_date_time = recs.delivery_id.hand_off_date_time - datetime.timedelta(days=1)
            if recs.delivery_id.date_done:
                recs.delivery_id.date_done = recs.delivery_id.date_done - datetime.timedelta(days=1)
            # if recs.delivery_id.scheduled_date:
            #     recs.delivery_id.scheduled_date = recs.delivery_id.scheduled_date - datetime.timedelta(days=1)
            if recs.delivery_id.delay_alert_date:
                recs.delivery_id.delay_alert_date = recs.delivery_id.delay_alert_date - datetime.timedelta(days=1)
