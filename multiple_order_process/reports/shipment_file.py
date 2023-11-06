from time import strftime, strptime
from odoo import models, fields, api
from datetime import datetime

class ShipmentFileWizard(models.TransientModel):
    _name = 'shipment.file.wizard'

    company = fields.Many2one('res.partner', 'Company', required=True)
    from_date = fields.Datetime('From Date', required=True)
    to_date = fields.Datetime('To Date', required=True)
    is_wip = fields.Boolean('WIP')
    is_cancelled = fields.Boolean('Cancelled')
    is_dispatched = fields.Boolean('Dispatched')
    is_delivered = fields.Boolean('Delivered')
    is_returned = fields.Boolean('Returned')
    is_re_dispatched = fields.Boolean('Re-Dispatched')
    # is_re_delivered = fields.Boolean('Re-Delivered')
    only_re_dispatched = fields.Boolean('Only Re-Dispatched')

    def generate_shipment_file(self):
        return self.env.ref('multiple_order_process.shipment_file_report').report_action(self)

    @api.onchange('is_re_dispatched')
    def set_false(self):
        self.only_re_dispatched = False

class ShipmentReport(models.AbstractModel):
    _name = 'report.multiple_order_process.report_shipment_file_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet('Dispatch File')
        sheet.set_column(0, 18, 20)
        format1 = workbook.add_format({'bold': True})
        # date_style = workbook.add_format({'text_wrap': True, 'num_format': strftime('%d-%b-%y')})
        # date_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd-mm-yyyy'})

        row = 0
        col = 0
        sheet.write(row, col, 'ORDER_NO', format1)
        sheet.write(row, col + 1, 'ITEM_CODE', format1)
        sheet.write(row, col + 2, 'ITEM_DESC', format1)
        sheet.write(row, col + 3, 'QTY', format1)
        sheet.write(row, col + 4, 'AWBNO', format1)
        sheet.write(row, col + 5, 'DESPATCH_DATE', format1)
        sheet.write(row, col + 6, 'DELIVERED_TO', format1)
        sheet.write(row, col + 7, 'DELIVERY_DATE', format1)
        sheet.write(row, col + 8, 'RTOREASON', format1)
        # Latest Dispatch Column
        sheet.write(row, col + 9, 'SDAWBNO', format1)
        sheet.write(row, col + 10, 'SDDESP_DT', format1)
        sheet.write(row, col + 11, 'SDDELI_DT', format1)
        sheet.write(row, col + 12, 'SDDELI_DTL', format1)
        sheet.write(row, col + 13, 'STATUS', format1)
        sheet.write(row, col + 14, 'DOCKET_NO', format1)
        sheet.write(row, col + 15, 'REJECTED_DT', format1)
        sheet.write(row, col + 16, 'WIP_DT', format1)
        sheet.write(row, col + 17, 'COURIER', format1)

        requested_status = []
        if lines.is_wip == True:
            requested_status = requested_status + ['wip', 'hand_off', 'ready', 'not_serviceable']
        if lines.is_cancelled == True:
            requested_status = requested_status + ['cancelled']
        if lines.is_dispatched == True:
            requested_status = requested_status + ['dispatched']
        if lines.is_delivered == True:
            requested_status = requested_status + ['delivered']
        if lines.is_returned == True:
            requested_status = requested_status + ['returned']
        if lines.is_re_dispatched == True:
            requested_status = requested_status + ['re_dispatched']
        # if lines.is_re_delivered == True:
        #     requested_status = requested_status + ['re_delivered']
        if lines.only_re_dispatched == True:
            requested_status = requested_status + ['only_re_dispatched']

        pemt_rec = self.env['pemt.rec'].search([])
        for rec in pemt_rec:
            if rec.customer_name.parent_id == lines.company and lines.from_date <= rec.up_date <= lines.to_date and rec.try_no_type == '0' and rec.order_status in requested_status and rec.try_no_type == '0':
                if 'only_re_dispatched' not in requested_status:
                    sheet.write(row + 1, col, rec.ref_no)
                    sheet.write(row + 1, col + 1, rec.item_code)
                    sheet.write(row + 1, col + 2, rec.item_desc)
                    sheet.write(row + 1, col + 3, rec.qty)
                    if rec.awb_nos:
                        sheet.write(row + 1, col + 4, rec.awb_nos.awb_number)
                    if rec.dispatched_on:
                        sheet.write(row + 1, col + 5, rec.dispatched_on)
                    if rec.person_delv:
                        sheet.write(row + 1, col + 6, rec.person_delv)
                    if rec.pod_date:
                        sheet.write(row + 1, col + 7, rec.pod_date)
                    if rec.return_reason:
                        sheet.write(row + 1, col + 8, rec.return_reason)
                    if rec.order_status == 'wip' or rec.order_status == 'hand_off' or rec.order_status == 'ready' or rec.order_status == 'not_serviceable':
                        sheet.write(row + 1, col + 13, 'WIP')
                    if rec.order_status == 'cancelled':
                        sheet.write(row + 1, col + 13, 'Cancelled')
                    if rec.order_status == 'dispatched':
                        sheet.write(row + 1, col + 13, 'Dispatched')
                    if rec.order_status == 'delivered':
                        sheet.write(row + 1, col + 13, 'Delivered')
                    if rec.order_status == 'returned':
                        sheet.write(row + 1, col + 13, 'Returned')
                    if rec.order_status == 're_dispatched':
                        sheet.write(row + 1, col + 13, 'Re-Dispatched')
                    if rec.awb_nos:
                        sheet.write(row + 1, col + 17, rec.awb_nos.serviced_awb_link.name)

                    row += 1

                if 'only_re_dispatched' in requested_status:
                    tries_list = []
                    for sub_rec in rec.try_lines:
                        tries_list.append(int(sub_rec.try_no_type))
                    for child_rec in rec.try_lines:
                        if child_rec.try_no_type == str(max(tries_list)):

                            if requested_status == ['re_dispatched', 'only_re_dispatched']:
                                if child_rec.order_status == False:
                                    sheet.write(row + 1, col, child_rec.ref_no)
                                    sheet.write(row + 1, col + 1, child_rec.item_code)
                                    sheet.write(row + 1, col + 2, child_rec.item_desc)
                                    sheet.write(row + 1, col + 3, child_rec.qty)
                                    if rec.awb_nos:
                                        sheet.write(row + 1, col + 4, rec.awb_nos.awb_number)
                                    if rec.dispatched_on:
                                        sheet.write(row + 1, col + 5, rec.dispatched_on)
                                    if rec.person_delv:
                                        sheet.write(row + 1, col + 6, rec.person_delv)
                                    if rec.pod_date:
                                        sheet.write(row + 1, col + 7, rec.pod_date)
                                    if rec.return_reason:
                                        sheet.write(row + 1, col + 8, rec.return_reason)
                                    if child_rec.awb_nos:
                                        sheet.write(row + 1, col + 9, child_rec.awb_nos.awb_number)
                                    if child_rec.dispatched_on:
                                        sheet.write(row + 1, col + 10, child_rec.dispatched_on)
                                    if child_rec.pod_date:
                                        sheet.write(row + 1, col + 11, child_rec.pod_date)
                                    if child_rec.person_delv:
                                        sheet.write(row + 1, col + 12, child_rec.person_delv)
                                    if child_rec.order_status == 'wip' or child_rec.order_status == 'hand_off' or child_rec.order_status == 'ready' or child_rec.order_status == 'not_serviceable':
                                        sheet.write(row + 1, col + 13, 'WIP')
                                    if child_rec.order_status == 'cancelled':
                                        sheet.write(row + 1, col + 13, 'Cancelled')
                                    if child_rec.order_status == 'dispatched':
                                        sheet.write(row + 1, col + 13, 'Dispatched')
                                    if child_rec.order_status == 'delivered':
                                        sheet.write(row + 1, col + 13, 'Re-Delivered')
                                    if child_rec.order_status == 'returned':
                                        sheet.write(row + 1, col + 13, 'Returned')
                                    if child_rec.order_status == 're_dispatched':
                                        sheet.write(row + 1, col + 13, 'Re-Dispatched')
                                    if child_rec.awb_nos:
                                        sheet.write(row + 1, col + 17, child_rec.awb_nos.serviced_awb_link.name)
                                    row += 1


                            else:
                                print(rec, child_rec, "plllololololo")
                                if child_rec.order_status in requested_status:
                                    sheet.write(row + 1, col, child_rec.ref_no)
                                    sheet.write(row + 1, col + 1, child_rec.item_code)
                                    sheet.write(row + 1, col + 2, child_rec.item_desc)
                                    sheet.write(row + 1, col + 3, child_rec.qty)
                                    if rec.awb_nos:
                                        sheet.write(row + 1, col + 4, rec.awb_nos.awb_number)
                                    if rec.dispatched_on:
                                        sheet.write(row + 1, col + 5, rec.dispatched_on)
                                    if rec.person_delv:
                                        sheet.write(row + 1, col + 6, rec.person_delv)
                                    if rec.pod_date:
                                        sheet.write(row + 1, col + 7, rec.pod_date)
                                    if rec.return_reason:
                                        sheet.write(row + 1, col + 8, rec.return_reason)
                                    if child_rec.awb_nos:
                                        sheet.write(row + 1, col + 9, child_rec.awb_nos.awb_number)
                                    if child_rec.dispatched_on:
                                        sheet.write(row + 1, col + 10, child_rec.dispatched_on)
                                    if child_rec.pod_date:
                                        sheet.write(row + 1, col + 11, child_rec.pod_date)
                                    if child_rec.person_delv:
                                        sheet.write(row + 1, col + 12, child_rec.person_delv)
                                    if child_rec.order_status == 'wip' or child_rec.order_status == 'hand_off' or child_rec.order_status == 'ready' or child_rec.order_status == 'not_serviceable':
                                        sheet.write(row + 1, col + 13, 'WIP')
                                    if child_rec.order_status == 'cancelled':
                                        sheet.write(row + 1, col + 13, 'Cancelled')
                                    if child_rec.order_status == 'dispatched':
                                        sheet.write(row + 1, col + 13, 'Dispatched')
                                    if child_rec.order_status == 'delivered':
                                        sheet.write(row + 1, col + 13, 'Re-Delivered')
                                    if child_rec.order_status == 'returned':
                                        sheet.write(row + 1, col + 13, 'Returned')
                                    if child_rec.order_status == 're_dispatched':
                                        sheet.write(row + 1, col + 13, 'Re-Dispatched')
                                    if child_rec.awb_nos:
                                        sheet.write(row + 1, col + 17, child_rec.awb_nos.serviced_awb_link.name)

                                    row += 1