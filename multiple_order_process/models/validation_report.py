import re

from odoo import api, models, fields, _

class ValidationReport(models.AbstractModel):
    _name = 'report.multiple_order_process.report_validation_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet('Error Page 1')
        sheet.set_column(0, 45, 30)
        format1 = workbook.add_format({'bold': True})
        format2 = workbook.add_format({'bg_color': 'yellow'})

        sheet.write(0, 0, 'UNIQUE REF', format1)
        sheet.write(0, 1, 'REFERENCE NO', format1)
        sheet.write(0, 2, 'ITEM CODE', format1)
        sheet.write(0, 3, 'QTY', format1)
        sheet.write(0, 4, 'ZIP CODE', format1)
        sheet.write(0, 5, 'EMAIL ID', format1)

        row = 0
        for n in lines:
            row += 1
            col = 0
            sheet.write(row, col, n.unique_ref)
            sheet.write(row, col + 1, n.ref_no)  # reference no
            sheet.write(row, col + 2, n.item_code)  # WS-OUT-ITEM-CODE
            sheet.write(row, col + 3, n.qty)  # WS-OUT-QTY
            sheet.write(row, col + 4, n.zip_code)  # zip-code
            sheet.write(row, col + 5, n.email_id)  # EMAIL-ID

            if n.qty <= n.global_item_code.qty_available and n.qty != 0:
                pass
            else:
                sheet.write(row, col + 3, n.qty, format2)

            if n.email_id:
                v_field40 = re.match('^[_a-z0-9A-Z-]+(\.[_a-z0-9A-Z-]+)*@[a-z0-9A-Z-]+(\.[a-z0-9A-Z-]+)*(\.[a-zA-Z]{2,4})$', n.email_id.strip())
                if v_field40 == None:
                    sheet.write(row, col + 5, n.email_id, format2)
            else:
                sheet.write(row, col + 5, n.email_id, format2)

            if n.zip_code:
                v_field33 = re.match('^\d{6}$', n.zip_code.strip())
                if v_field33 == None:
                    sheet.write(row, col + 4, n.zip_code, format2)
            else:
                sheet.write(row, col + 4, n.zip_code, format2)

            n.validated = True