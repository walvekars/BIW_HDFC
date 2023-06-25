from odoo import models, fields, api

class CourierPriority(models.Model):
    _name = 'courier.priority'

    priority_no = fields.Integer(string='Priority No.', required=True)
    name = fields.Char(string='Priority No / Name')
    courier_company = fields.Many2one('res.partner', string='Courier Company', required=True, ondelete="restrict")

    _sql_constraints = [
        ('unique_priority_no', 'unique (priority_no)', 'Duplicate priorities are not allowed'),
        ('unique_courier_company', 'unique (courier_company)', 'Duplicate priorities are not allowed')
    ]

    @api.constrains('priority_no')
    def create_name(self):
        self.name = self.priority_no

class CourierContacts(models.Model):
    _inherit = 'res.partner'

    courier_details = fields.Boolean(string='Courier Company')
    awb_no_unassigned = fields.Integer(string='AWB No. Unassigned', compute='awb_no_unassigned_count')
    courier_pincode_ids = fields.One2many('courier.company.code', 'courier_company', readonly=True)
    serviced_awb = fields.One2many('air.way.bill', 'serviced_awb_link', readonly=True)
    courier_account_number = fields.Char(string='Courier Account Number')
    priority_link = fields.One2many('courier.priority', 'courier_company')
    priority_no = fields.Char(string='Priority No.', related='priority_link.name', readonly=True)

    def awb_no_unassigned_count(self):
        if self.courier_details:
            lines = []
            lines_done = []
            for line in self.serviced_awb:
                lines.append(line)
                if line.delivery_order_number:
                    lines_done.append(line)
            self.awb_no_unassigned = len(lines) - len(lines_done)
        else:
            self.awb_no_unassigned = False

class AirWayBill(models.Model):
    _name = 'air.way.bill'
    _rec_name = 'awb_number'

    awb_number = fields.Char(string="AWB Number")
    delivery_order_number = fields.Many2one('stock.picking', string="Delivery Order Number")
    serviced_awb_link = fields.Many2one('res.partner', string='Courier Company', ondelete="restrict")

class CourierCompanyCode(models.Model):
    _name = 'courier.company.code'
    # _rec_name = 'pin_code'

    courier_company = fields.Many2one('res.partner', ondelete="restrict", string='Courier Partner')
    pin_code = fields.Char(string='PIN CODE')
    location = fields.Char(string='LOCATION')
    state = fields.Char(string='STATE')
    hub = fields.Char(string='HUB')
    airport = fields.Char(string='AIRPORT')
    tier = fields.Char(string='TIER')

    def name_get(self):
        result = []
        for record in self:
            if self.env.context.get('custom_pin_name', False):
                result.append((record.id, "{}".format(record.pin_code)))
            else:
                result.append((record.id, "{}".format(record.courier_company.name)))
        return result


class ClientCatalogue(models.Model):
    _name = 'client.catalogue'

    global_code = fields.Many2one('product.template', string='Global Code', ondelete='restrict', required=True)
    client = fields.Many2one('res.partner', string='Client', domain="[('is_company', '=', True), ('courier_details', '=', False)]", ondelete='restrict', required=True)
    client_code = fields.Char(string='Client Code', required=True)

    def name_get(self):
        res = []
        for records in self:
            res.append((records.id, '%s %s' % (records.client, records.global_code)))
        return res