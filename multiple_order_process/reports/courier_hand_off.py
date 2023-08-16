from odoo import api, models, fields, _
import cups

class HandOffReport(models.TransientModel):
    _name = 'handoff.wizard'

    date = fields.Date()
    sel_hand_off = fields.Many2one('stock.picking')
    log_user = fields.Char(string="Employee", default=lambda self: self.env.user.name)

    @api.onchange('date')
    def date_handoff_id(self):
        handoff_list = []
        dup_handoff_list = []
        stock_picking = self.env['stock.picking'].search([])
        for rec in stock_picking:
            if self.date and rec.hand_off_date_time:
                if self.date == rec.hand_off_date_time.date():
                    if rec.hand_off_id not in dup_handoff_list:
                        handoff_list.append(rec.id)
                        dup_handoff_list.append(rec.hand_off_id)
        return {'domain': {'sel_hand_off': [('id', 'in', handoff_list)]}}

    def generate_courier_handoff(self):
        return self.env.ref('multiple_order_process.handoff_file_report').report_action(self)

    def courier_hand_off_printing(self):
        file, file_type = self.env.ref('multiple_order_process.handoff_file_report')._render_qweb_pdf(res_ids=self._ids)
        conn = cups.Connection()
        f = open('hand_off.pdf', 'wb')
        f.write(file)
        f.close()
        printers = conn.getPrinters()
        for printer_name in printers:
            if printer_name:
                conn.printFile(printer_name, 'hand_off.pdf', '', {})
