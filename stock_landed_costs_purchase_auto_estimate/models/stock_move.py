from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_estimated_landed_cost(self):
        """Estimated landed cost of this move, in company currency: the
        vendor indirect cost percentage applied to the purchase line subtotal
        pro rata of the quantity of the move (received quantity once done,
        demand before)."""
        self.ensure_one()
        line = self.purchase_line_id
        if not line or line.product_uom_id.is_zero(line.product_qty):
            return 0.0
        percent = line.order_id._get_estimated_cost_percent(line)
        if not percent:
            return 0.0
        quantity = self.quantity if self.state == "done" else self.product_uom_qty
        quantity = self.product_uom._compute_quantity(quantity, line.product_uom_id)
        company = line.company_id
        return line.currency_id._convert(
            line.price_subtotal * quantity / line.product_qty * percent / 100,
            company.currency_id,
            company,
            line.date_planned or fields.Date.context_today(line),
        )
