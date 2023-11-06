from time import strftime, strptime
from odoo import models, fields, api


class InvoiceSupportingReport(models.AbstractModel):
    _name = 'report.multiple_order_process.report_invoice_supporting'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet('Invoice Supporting')
        format1 = workbook.add_format({'bold': True})
        date_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd/mm/yyyy'})

        sheet.set_column(0, 23, 20)

        row = 0
        col = 0
        sheet.write(row, col,'COMMON FIELD', format1)
        sheet.write(row, col + 1, 'RECEIVED Or IMPORT DATE', format1)
        sheet.write(row, col + 2, 'FILE NAME', format1)
        sheet.write(row, col + 3, 'Order NUMBER', format1)
        # sheet.write(row, col + 4, 'COMMON FIELD', format1)
        sheet.write(row, col + 4, 'ITEM CODE', format1)
        sheet.write(row, col + 5, 'ITEM DESC', format1)
        sheet.write(row, col + 6, 'CLIENT QTY', format1)
        sheet.write(row, col + 7, 'DISP DATE', format1)
        sheet.write(row, col + 8, 'REDISP DATE', format1)
        sheet.write(row, col + 9, 'REDISP AWB no', format1)
        sheet.write(row, col + 10, 'STATUS', format1)
        sheet.write(row, col + 11, 'AWB Number', format1)
        sheet.write(row, col + 12, 'COURIER NAME', format1)
        sheet.write(row, col + 13, 'Delivered to', format1)
        sheet.write(row, col + 14, 'Delivered Date', format1)
        sheet.write(row, col + 15, 'REDelivered to', format1)

        sheet.write(row, col + 16, 'REDelivered Date', format1)
        sheet.write(row, col + 17, 'GST%', format1)
        sheet.write(row, col + 18, 'Unit Price W/O GST', format1)
        sheet.write(row, col + 19, 'Total Price W/O GST', format1)
        sheet.write(row, col + 20, 'Unit Price W GST', format1)
        sheet.write(row, col + 21, 'Total Price W GST', format1)
        # sheet.write(row, col + 22, 'Client Invoice No', format1)
        for rec in lines:
            if rec.move_type == "out_refund":
                sheet.write(row, col + 22, 'Credit Note Number', format1)
                sheet.write(row, col + 23, 'Invoice Number', format1)
            else:
                sheet.write(row, col + 22, 'Client Invoice No', format1)

        for invoice in lines:
            for rec in invoice.compressed_invoice_change:
                sheet.write(row + 1, col, rec.customer_ref)
                pemt_rec = self.env['pemt.rec'].search([('unique_ref', '=', rec.customer_ref)])
                if pemt_rec.up_date:
                    sheet.write(row + 1, col + 1, pemt_rec.up_date.strftime('%d-%b-%y'))
                sheet.write(row + 1, col + 2, pemt_rec.file_name.name,)
                sheet.write(row + 1, col + 3, pemt_rec.ref_no,)
                # sheet.write(row + 1, col+4, rec.customer_ref)
                sheet.write(row + 1, col+4, pemt_rec.item_code,)
                sheet.write(row + 1, col+5, pemt_rec.item_desc,)
                sheet.write(row + 1, col+6, pemt_rec.qty,)
                if(pemt_rec.dispatched_on):
                    sheet.write(row + 1, col + 7, pemt_rec.dispatched_on.strftime('%d-%b-%y'), )
                    ''''dout for redispatch date and redispatch awb number'''







                if(pemt_rec.order_status):
                    sheet.write(row + 1, col + 10, pemt_rec.order_status, )
                if(pemt_rec.awb_nos):
                    sheet.write(row + 1, col + 11, pemt_rec.awb_nos.awb_number, )
                if (pemt_rec.courier):
                    sheet.write(row + 1, col + 12, pemt_rec.courier.courier_company.name, )
                if (pemt_rec.person_delv):
                    print('persaon delivered         cd.................',pemt_rec.person_delv)
                    sheet.write(row + 1, col + 13, pemt_rec.person_delv, )
                else:
                    sheet.write(row + 1, col + 13, ' ', )

                if (pemt_rec.pod_date):
                    sheet.write(row + 1, col + 14, pemt_rec.pod_date.strftime('%d-%b-%y'), )



                ''''dout for redelivered to  and redelivered date awb '''





                sheet.write(row + 1, col + 17,rec.tax, )
                sheet.write(row + 1, col+18, rec.product_unit_price,)
                sheet.write(row + 1, col+19, rec.total,)
                a = (''.join(i for i in rec.tax if i.isdigit()))
                # tax = ((int(a)/100) * rec.product_unit_price)
                tax_amount = ((int(a) / 100) * rec.product_unit_price) + rec.product_unit_price
                tot_tax_amount = tax_amount * rec.compress_product_quantity
                sheet.write(row + 1, col+20, tax_amount,)
                sheet.write(row + 1, col+21, tot_tax_amount,)
                sheet.write(row + 1, col + 22, invoice.name)
                if invoice.move_type == "out_refund":
                    stock_picking = self.env['stock.picking'].search([('name', '=', rec.delivery_ref)])
                    sheet.write(row + 1, col + 23, stock_picking.invoiced_id.name)





                row = row + 1



