from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    stock_landed_costs_ids = fields.Many2many(
        "stock.landed.cost",
        "stock_landed_cost_stock_picking_rel",
        "stock_picking_id",
        "stock_landed_cost_id",
        string="Landed Costs",
        copy=False,
    )

    def button_validate(self):
        res = super().button_validate()
        done_pickings = self.filtered(lambda p: p.state == "done")
        done_pickings.sudo().stock_landed_costs_ids.filtered(
            lambda x: x.state == "draft"
        )._refresh_estimate().button_validate()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        self.sudo().stock_landed_costs_ids.filtered(
            lambda x: x.state == "draft"
        ).button_cancel()
        return res
