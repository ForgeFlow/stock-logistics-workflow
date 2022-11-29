# Copyright 2022 ForgeFlow
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockMoveSaleLine(models.TransientModel):
    _name = "stock.move.sale.wizard"
    _description = "Stock Move Sale Wizard"

    item_ids = fields.One2many(
        comodel_name="stock.move.sale.wizard.item",
        inverse_name="wiz_id",
        string="Items"
    )

    @api.model
    def _prepare_item(self, line):
        return {
            "wiz_id": self.id,
            "line_id": line.id,
            "sequence2": line.sequence2,
            "product_id": line.product_id.id,
            "commitment_date": line.commitment_date,
            "product_uom_qty": line.product_uom_qty,
        }

    @api.model
    def get_items(self, sale_lines):
        items = []
        for line in sale_lines:
            items.append([0, 0, self._prepare_item(line)])
        return items

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_line_ids = self.env.context["sale_line_ids"] or []
        sale_lines = self.env['sale.order.line'].browse(active_line_ids)
        res["item_ids"] = self.get_items(sale_lines)
        return res

    def change_sale_line(self):
        move_id = self.env.context["active_id"]
        move = self.env['stock.move'].browse(move_id)
        sale_line = False
        for line in self.item_ids:
            if line.select_me and not sale_line:
                sale_line = line
            elif line.select_me and sale_line:
                raise ValidationError(_("Select just one line to assign it to the move."))
        if sale_line:
            move.write({"sale_line_id": sale_line.line_id})


class StockMoveSaleLineItem(models.TransientModel):
    _name = "stock.move.sale.wizard.item"
    _description = "Stock Move Sale Wizard Items"

    wiz_id = fields.Many2one(comodel_name="stock.move.sale.wizard", string="Wizard")
    line_id = fields.Integer()
    sequence2 = fields.Integer(string="Line Number")
    product_id = fields.Many2one(string="Product", comodel_name="product.product")
    commitment_date = fields.Date(string="Delivery Date", required=True)
    product_uom_qty = fields.Float(string="Quantity")
    select_me = fields.Boolean(string="", default=False)
