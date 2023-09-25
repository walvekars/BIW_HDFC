# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime


class UpdateOrders(models.Model):
    _name = 'update.rec'

    awb_nos = fields.Char(string='AWB NO')
    pod_date = fields.Date(string='DELIVERED ON')
    person_delv = fields.Char(string='PERSON DELIVERED')
    return_date = fields.Date(string='RETURNED ON')
    return_reason = fields.Char(string='RETURN REASON')
    cancel_order = fields.Char(string='ORDER NUMBER')
    cancel_date = fields.Date(string='CANCELED ON')
    cancel_reason = fields.Char(string='CANCEL REASON')
    name = fields.Char(string='NAME')
    add1 = fields.Char(string='ADD1')
    add2 = fields.Char(string='ADD2')
    city = fields.Char(string='CITY')
    pin = fields.Char(string='PINCODE')
    phone = fields.Char(string='PHONE')
    email = fields.Char(string='EMAIL')

class UpdateMasterWizard(models.TransientModel):
    _name = 'update.master.wizard'

    # courier1 = fields.Many2one('res.partner', string='Courier', domain="[('is_company','=', True), ('courier_details','=', True)]")
    to_update = fields.Selection([('delivery', 'Delivered'), ('return', 'Returned'), ('cancelled', 'Cancelled'),
                                  ('returned_n_reshipped', 'Re-Dispatch')], required=True, string='To Update as')

    def update_master_action_submit(self):
        # selected ids in list
        selected_ids = self.env.context.get('active_ids', [])

        # converting selected ids to record tuple
        selected_records = self.env['update.rec'].browse(selected_ids)

        awb_no = [rlist.awb_nos.awb_number for rlist in self.env['pemt.rec'].search([]) if rlist.awb_nos]
        order_no = [rlist.ref_no.strip() for rlist in self.env['pemt.rec'].search([]) if rlist.ref_no]
        company_ids = []
        # company_ids = [rlist.customer_name.parent_id for rlist in self.env['pemt.rec'].search([]) if rlist.customer_name.parent_id]
        vals = []
        delete = []
        created_retry_line = []

        for lines in selected_records:
            if lines.awb_nos:
                awb_no_searched = self.env['pemt.rec'].search([('awb_nos', '=', lines.awb_nos.strip())])
            if lines.cancel_order:
                order_no_searched = self.env['pemt.rec'].search([('ref_no', '=', lines.cancel_order.strip())])

            if self.to_update == 'delivery':
                if lines.awb_nos.strip():
                    if lines.awb_nos.strip() in awb_no:
                        # if lines.awb_nos == awb_no_searched.awb_nos:
                        if awb_no_searched.order_status == 'dispatched':
                            if lines.pod_date and lines.pod_date > awb_no_searched.dispatched_on:
                                awb_no_searched.update({
                                    'pod_date': lines.pod_date,
                                    'person_delv': lines.person_delv,
                                    'up_pod_date': datetime.date.today()
                                })
                                awb_no_searched.delivery_id.order_status = 'delivered'
                                delete.append(lines.id)
                                # lines.unlink()
                            else:
                                raise UserError("date should be greater than Dispatched date")
                        else:
                            raise UserError('Order must be "Dispatched" to set the order as "Delivered"')
                    else:
                        raise UserError("AWB Number Doesn't exist")
                else:
                    raise UserError("Empty AWB Number")

            if self.to_update == 'return':
                if lines.awb_nos:
                    if lines.awb_nos.strip() in awb_no:
                        return_list = []
                        if awb_no_searched.order_status == 'dispatched' or awb_no_searched.order_status == 'delivered':
                            if awb_no_searched.order_status == 'dispatched':
                                if lines.return_date and lines.return_date > awb_no_searched.dispatched_on:
                                    return_list.append(True)
                                else:
                                    return_list.append(False)
                                    raise UserError("Date should be greater than dispatched date")
                            if awb_no_searched.order_status == 'delivered':
                                if lines.return_date and lines.return_date > awb_no_searched.up_pod_date:
                                    return_list.append(True)
                                else:
                                    return_list.append(False)
                                    raise UserError("Date should be greater than Delivered Date")
                        else:
                            raise UserError(
                                'Order must be either "Dispatched" or "Delivered" to set the order as "Returned"')
                        if sum(return_list) == True:
                            order = self.env['stock.picking'].search(
                                [('picking_type_code', '=', 'outgoing'), ('awb_number', '=', lines.awb_nos)])
                            stock_return_picking = self.env['stock.return.picking'].create({'picking_id': order.id})
                            stock_return_picking._onchange_picking_id()
                            stock_return_picking_line = stock_return_picking.product_return_moves
                            stock_return_picking_line.update({
                                'quantity': order.move_ids_without_package.quantity_done
                            })
                            x = stock_return_picking.create_returns()
                            return_order = self.env['stock.picking'].search([('id', '=', x['res_id'])])
                            return_order.action_set_quantities_to_reservation()
                            return_order.button_validate()
                            order.return_order = return_order
                            awb_no_searched.update({
                                'return_date': lines.return_date,
                                'return_reason': lines.return_reason,
                                'up_return_date': datetime.date.today()
                            })
                            awb_no_searched.delivery_id.order_status = 'returned'  # changed
                            # lines.unlink()
                            delete.append(lines.id)
                    else:
                        raise UserError("AWB Number Doesn't exist")
                else:
                    raise UserError("Empty AWB Number")


            if self.to_update == 'cancelled':
                if lines.cancel_order:
                    if lines.cancel_order.strip() in order_no:
                        if order_no_searched.order_status == 'wip' or order_no_searched.order_status == 'ready' or order_no_searched.order_status == 'not_serviceable' or order_no_searched.order_status == 'hand_off' or order_no_searched.order_status == 'returned':
                            # Ready and not Serviceable is also meant as Work in Progress
                            if order_no_searched.order_status == 'wip' or order_no_searched.order_status == 'ready' or order_no_searched.order_status == 'not_serviceable':
                                if lines.cancel_date and lines.cancel_date >= order_no_searched.up_date.date():
                                    self.env['stock.picking'].search(
                                        [('unique_ref', '=', order_no_searched.unique_ref),
                                         ('picking_type_code', '=', 'outgoing')]).action_cancel()
                                    order_no_searched.update({
                                        'cancel_date': lines.cancel_date,
                                        'cancel_reason': lines.cancel_reason,
                                    })
                                    order_no_searched.delivery_id.order_status = 'cancelled'  # changed
                                    # lines.unlink()
                                    delete.append(lines.id)
                                else:
                                    raise UserError(
                                        'Date should be greater than or equal to Order upload Date')
                            if order_no_searched.order_status == 'hand_off':
                                if lines.cancel_date and lines.cancel_date >= order_no_searched.hand_off_date:
                                    self.env['stock.picking'].search(
                                        [('unique_ref', '=', order_no_searched.unique_ref),
                                         ('picking_type_code', '=', 'outgoing')]).action_cancel()
                                    order_no_searched.update({
                                        'cancel_date': lines.cancel_date,
                                        'cancel_reason': lines.cancel_reason,
                                    })
                                    order_no_searched.delivery_id.order_status = 'cancelled'  # changed
                                    # lines.unlink()
                                    delete.append(lines.id)
                                else:
                                    raise UserError('Date should be greater than or equal to hand-off Date')
                            if order_no_searched.order_status == 'returned':
                                if lines.cancel_date and lines.cancel_date > order_no_searched.up_return_date:
                                    #         # temporary -  for patch purpose, (Order returned in master sheet and manually updated the quantity to inventory, but status in delivery order still remains Dispatched "Done status" so upcoming orders will be erp flow untill 27/02/2023)
                                    if self.env['stock.picking'].search(
                                            [('unique_ref', '=', order_no_searched.unique_ref),
                                             ('picking_type_code', '=', 'outgoing')]).state == 'done':
                                        order_no_searched.update({
                                            'cancel_date': lines.cancel_date,
                                            'cancel_reason': lines.cancel_reason,
                                        })
                                        order_no_searched.delivery_id.order_status = 'cancelled'  # changed
                                        # lines.unlink()
                                        delete.append(lines.id)
                                    #         # temporary -  for patch purpose, (Order returned in master sheet and manually updated the quantity to inventory, but status in delivery order still remains Dispatched "Done status" so upcoming orders will be erp flow untill 27/02/2023)
                                    else:
                                        self.env['stock.picking'].search(
                                            [('unique_ref', '=', order_no_searched.unique_ref),
                                             ('picking_type_code', '=', 'outgoing')]).action_cancel()
                                        order_no_searched.update({
                                            'cancel_date': lines.cancel_date,
                                            'cancel_reason': lines.cancel_reason,
                                        })
                                        order_no_searched.delivery_id.order_status = 'cancelled'  # changed
                                        # lines.unlink()
                                        delete.append(lines.id)
                                else:
                                    raise UserError('Date should be greater than Return Date')
                        else:
                            raise UserError(
                                "Order must be either 'WIP', 'Ready', 'Not Serviceable', 'Hand-off' or 'Returned' to set the order as 'Cancelled'")
                    else:
                        raise UserError("Order Number Doesn't exist")
                else:
                    raise UserError("Empty Order Number")

            if self.to_update == 'returned_n_reshipped':  # To do this mapping customer(address_id_map) is must in master sheet
                if lines.awb_nos:
                    if lines.awb_nos.strip() in awb_no:
                        if awb_no_searched.order_status == 'returned':
                            if datetime.date.today() > awb_no_searched.up_return_date:    # bhjfjvhjvbhvbdvbhdsvbhdsvb should be uncommented and send..............................................................

                                tries_list = []
                                parent_awb = ''
                                if awb_no_searched.parent_line.id == False:
                                    tries_list.append(0)
                                    parent_awb = awb_no_searched
                                    company_ids.append(awb_no_searched.customer_name.parent_id)
                                else:
                                    parent_awb = awb_no_searched.parent_line
                                    company_ids.append(awb_no_searched.parent_line.customer_name.parent_id)
                                    for recs in awb_no_searched.parent_line.try_lines:
                                        tries_list.append(recs.try_no_type)
                                print(parent_awb)

                                tries_available = []
                                for tries in self.env['multi.try'].search([]):
                                    tries_available.append(int(tries.type))

                                if int(max(tries_list)) < max(tries_available):
                                    new_try = self.env['multi.try'].search([('type', '=', str(int(max(tries_list)) + 1))])

                                    order = parent_awb.try_lines.create({
                                        'parent_line': parent_awb.id,
                                        'unique_ref': parent_awb.unique_ref,
                                        'file_name': parent_awb.file_name.id,
                                        'up_date': parent_awb.up_date,
                                        'ref_no': parent_awb.ref_no,
                                        'item_code': parent_awb.item_code,
                                        'item_desc': parent_awb.item_desc,
                                        'global_item_code': parent_awb.global_item_code.id,
                                        'qty': parent_awb.qty,
                                    })

                                    contact = parent_awb.customer_name.create({
                                        'unique_ref': order.id,
                                        'parent_id': parent_awb.customer_name.id,
                                        'type': 'delivery',
                                        'company_type': 'person',
                                        'tries': new_try.id,
                                        'name': lines.name,
                                        'street': lines.add1,
                                        'street2': lines.add2,
                                        'city': lines.city,
                                        'zip': lines.pin,
                                        'mobile': lines.phone,
                                        'email': lines.email
                                    })

                                    order.update({
                                        'customer_name': contact.id
                                    })

                                    created_retry_line.append(order)
                                    awb_no_searched.delivery_id.order_status = 're_dispatched'

                                    vals.append((0, 0, {
                                        'product_id': parent_awb.global_item_code.id,
                                        'name': parent_awb.item_desc,
                                        'contact_name': contact.id,
                                        'product_uom_qty': parent_awb.qty
                                    }))
                                    delete.append(lines.id)

                                else:
                                    raise UserError('Maximum Try Reached: ' + str(max(tries_available)))
                            else:
                                raise UserError("Can't Re-Dispatch the orders which are returned Today")   # bhjfjvhjvbhvbdvbhdsvbhdsvb should be uncommented and send..............................................................
                        else:
                            raise UserError('Order must be "Returned" to Re-Dispatch the order')
                    else:
                        raise UserError("AWB Number Doesn't exists")
                else:
                    raise UserError("Empty AWB Number")

        if self.to_update == 'returned_n_reshipped':
            if len(set(company_ids)) == 1:
                new_sale_order = self.env['sale.order'].create({
                    'state': 'draft',
                    'partner_id': company_ids[0].id,
                    'order_line': vals
                })

                for re_orders in created_retry_line:
                    re_orders.order_no = new_sale_order.id
            else:
                raise UserError("Select orders which are Related to one Company")

        self.env['update.rec'].search([('id', 'in', delete)]).unlink()