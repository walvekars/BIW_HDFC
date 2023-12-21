from time import strftime, strptime
from odoo import models, fields, api
from datetime import datetime

class ShipmentFileWizard(models.TransientModel):
    _name = 'shipment.file.wizard'

    company = fields.Many2one('res.partner', 'Company', required=True)

    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)

    is_wip = fields.Boolean('WIP')
    is_cancelled = fields.Boolean('Cancelled')
    is_dispatched = fields.Boolean('Dispatched')
    is_delivered = fields.Boolean('Delivered')
    is_returned = fields.Boolean('Returned')

    def generate_shipment_file(self):
        return self.env.ref('multiple_order_process.shipment_file_report').report_action(self)

    # @api.onchange('is_re_dispatched')
    # def set_false(self):
    #     self.only_re_dispatched = False

class ShipmentReport(models.AbstractModel):
    _name = 'report.multiple_order_process.report_shipment_file_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet('Dispatch File')
        sheet.set_column(0, 18, 20)
        format1 = workbook.add_format({'bold': True})
        date_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd-mm-yyyy'})

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

        if lines.is_wip == False and lines.is_cancelled == False and lines.is_dispatched == False and lines.is_dispatched == False and lines.is_delivered == False and lines.is_returned == False:
            pass
        else:
            count = 0
            requested_status.append('&')
            requested_status.append(('latest', '=', True))

            if lines.is_wip == True:
                # requested_status = requested_status + ['wip', 'hand_off', 'ready', 'not_serviceable']
                requested_status.append('&')
                requested_status.append(('wip_date', '>=', lines.from_date))
                requested_status.append(('wip_date', '<=', lines.to_date))
                count += 1
            if lines.is_cancelled == True:
                # requested_status = requested_status + ['cancelled']
                requested_status.append('&')
                requested_status.append(('cancel_date', '>=', lines.from_date))
                requested_status.append(('cancel_date', '<=', lines.to_date))
                count += 1
            if lines.is_dispatched == True:
                # requested_status = requested_status + ['dispatched']
                requested_status.append('&')
                requested_status.append(('dispatched_on', '>=', lines.from_date))
                requested_status.append(('dispatched_on', '<=', lines.to_date))
                count += 1
            if lines.is_delivered == True:
                # requested_status = requested_status + ['delivered']
                requested_status.append('&')
                requested_status.append(('up_pod_date', '>=', lines.from_date))
                requested_status.append(('up_pod_date', '<=', lines.to_date))
                count += 1
            if lines.is_returned == True:
                # requested_status = requested_status + ['returned']
                requested_status.append('&')
                requested_status.append(('up_return_date', '>=', lines.from_date))
                requested_status.append(('up_return_date', '<=', lines.to_date))
                count += 1

            # if lines.is_re_dispatched == True:
            #     # requested_status = requested_status + ['re_dispatched']
            #     requested_status.append(('up_return_date', '>=', lines.from_date))
            #     requested_status.append(('up_return_date', '<=', lines.to_date))

            # # if lines.is_re_delivered == True:
            # #     requested_status = requested_status + ['re_delivered']
            # if lines.only_re_dispatched == True:
            #     requested_status = requested_status + ['only_re_dispatched']

            print('requested_status - a', requested_status)
            for l in range(count - 1):
                requested_status.insert(2, '|')

        print('requested_status - b', requested_status)
        if len(requested_status) > 0:
            pemt_rec = self.env['pemt.rec'].search(requested_status)
            print(pemt_rec)

            print(len(pemt_rec), 'len()')

            for rec in pemt_rec:
                print(rec.parent_line, "parent_line")

                if not rec.parent_line.id:
                    sheet.write(row + 1, col, rec.ref_no)
                    sheet.write(row + 1, col + 1, rec.item_code)
                    sheet.write(row + 1, col + 2, rec.item_desc)
                    sheet.write(row + 1, col + 3, rec.qty)
                    if rec.awb_nos:
                        sheet.write(row + 1, col + 4, rec.awb_nos.awb_number)
                    if rec.dispatched_on:
                        sheet.write(row + 1, col + 5, rec.dispatched_on, date_style)
                    if rec.person_delv:
                        sheet.write(row + 1, col + 6, rec.person_delv)
                    if rec.pod_date:
                        sheet.write(row + 1, col + 7, rec.pod_date, date_style)
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
                    # if rec.order_status == 're_dispatched':
                    #     sheet.write(row + 1, col + 13, 'Re-Dispatched')
                    if rec.awb_nos:
                        sheet.write(row + 1, col + 17, rec.awb_nos.serviced_awb_link.name)
                    row += 1

                else:
                    sheet.write(row + 1, col, rec.ref_no)
                    sheet.write(row + 1, col + 1, rec.item_code)
                    sheet.write(row + 1, col + 2, rec.item_desc)
                    sheet.write(row + 1, col + 3, rec.qty)
                    if rec.parent_line.awb_nos:
                        sheet.write(row + 1, col + 4, rec.parent_line.awb_nos.awb_number)
                    if rec.parent_line.dispatched_on:
                        sheet.write(row + 1, col + 5, rec.parent_line.dispatched_on, date_style)
                    if rec.parent_line.person_delv:
                        sheet.write(row + 1, col + 6, rec.parent_line.person_delv)
                    if rec.parent_line.pod_date:
                        sheet.write(row + 1, col + 7, rec.parent_line.pod_date, date_style)
                    if rec.parent_line.return_reason:
                        sheet.write(row + 1, col + 8, rec.parent_line.return_reason)

                    if rec.awb_nos:
                        sheet.write(row + 1, col + 9, rec.awb_nos.awb_number)
                    if rec.dispatched_on:
                        sheet.write(row + 1, col + 10, rec.dispatched_on, date_style)
                    if rec.pod_date:
                        sheet.write(row + 1, col + 11, rec.pod_date, date_style)

                    if rec.order_status == 'wip' or rec.order_status == 'hand_off' or rec.order_status == 'ready' or rec.order_status == 'not_serviceable':
                        sheet.write(row + 1, col + 13, 'WIP')
                    if rec.order_status == 'cancelled':
                        sheet.write(row + 1, col + 13, 'Cancelled')
                    if rec.order_status == 'dispatched':
                        sheet.write(row + 1, col + 13, 'Re-Dispatched')
                    if rec.order_status == 'delivered':
                        sheet.write(row + 1, col + 13, 'Re-Delivered')
                    if rec.order_status == 'returned':
                        sheet.write(row + 1, col + 13, 'Re-Returned')
                    # if rec.order_status == 're_dispatched':
                    #     sheet.write(row + 1, col + 13, 'Re-Dispatched')
                    if rec.awb_nos:
                        sheet.write(row + 1, col + 17, rec.awb_nos.serviced_awb_link.name)
                    row += 1