from odoo import fields, models


class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    # same standard field, just here to clarify the table and column names
    picking_ids = fields.Many2many(
        "stock.picking",
        "stock_landed_cost_stock_picking_rel",
        "stock_landed_cost_id",
        "stock_picking_id",
        string="Transfers",
        copy=False,
    )

    def _refresh_estimate(self):
        """Rebuild the estimate cost lines from the moves actually received,
        so that a partial receipt is only charged for what it received and its
        backorder for the rest. Returns the landed costs that are kept."""
        to_unlink = self.browse()
        for cost in self.filtered(lambda c: c.state == "draft" and c.purchase_id):
            estimate_lines = cost.cost_lines.filtered("estimate")
            if not estimate_lines:
                continue
            moves = cost.picking_ids.move_ids.filtered(lambda m: m.state == "done")
            estimate_lines.unlink()
            vals_list = cost.purchase_id._prepare_estimated_cost_lines_vals(moves)
            if vals_list:
                cost.cost_lines = [(0, 0, vals) for vals in vals_list]
            if cost.cost_lines:
                cost.compute_landed_cost()
            else:
                to_unlink |= cost
        to_unlink.unlink()
        return self - to_unlink

    def compute_landed_cost(self):
        res = super().compute_landed_cost()
        for cost in self:
            for cost_line in cost.cost_lines.filtered("estimate"):
                cost._allocate_estimate_per_move(cost_line)
        return res

    def _allocate_estimate_per_move(self, cost_line):
        """Give each move the share of the estimate that its own vendor
        percentage and value produce, instead of the split method pooling the
        estimate across products with different percentages."""
        self.ensure_one()
        currency = self.currency_id
        adjustments = self.valuation_adjustment_lines.filtered(
            lambda a: a.cost_line_id == cost_line
        )
        weights = {
            adjustment: adjustment.move_id._get_estimated_landed_cost()
            if not cost_line.estimate_move_id
            or adjustment.move_id == cost_line.estimate_move_id
            else 0.0
            for adjustment in adjustments
        }
        total = sum(weights.values())
        if currency.is_zero(total):
            return
        allocated = 0.0
        for adjustment, weight in weights.items():
            value = currency.round(cost_line.price_unit * weight / total)
            adjustment.additional_landed_cost = value
            allocated += value
        difference = currency.round(cost_line.price_unit - allocated)
        if not currency.is_zero(difference):
            biggest = max(weights, key=weights.get)
            biggest.additional_landed_cost += difference


class StockLandedCostLines(models.Model):
    _inherit = "stock.landed.cost.lines"

    estimate = fields.Boolean(
        readonly=True,
        help="Line created from the vendor indirect cost estimate. It is "
        "recomputed from the received quantities when the transfer is "
        "validated.",
    )
    estimate_move_id = fields.Many2one(
        comodel_name="stock.move",
        readonly=True,
        help="Receipt move whose estimate this line carries, when the "
        "estimate keeps one line per purchased product.",
    )
