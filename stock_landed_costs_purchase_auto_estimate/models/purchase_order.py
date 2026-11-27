from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _get_estimated_cost_percent(self, line):
        """Indirect cost percentage of the order vendor for the line product."""
        if line.product_id.cost_method not in ("fifo", "average"):
            return 0.0
        supplierinfo = line.product_id.seller_ids.filtered(
            lambda x, line=line: x.partner_id == line.order_id.partner_id
        )[:1]
        return supplierinfo.indirect_cost_percent

    def _prepare_estimated_cost_line_vals(self, line, cost_price):
        """Legacy cost line: the purchased product, forced to the stock
        valuation account, so the estimate entry nets within that account."""
        return {
            "product_id": line.product_id.id,
            "name": line.product_id.name,
            "account_id": line.product_id.product_tmpl_id.get_product_accounts()[
                "stock_valuation"
            ].id,
            "price_unit": cost_price,
            "split_method": line.product_id.split_method_landed_cost or "equal",
            "estimate": True,
        }

    def _prepare_estimated_cost_product_line_vals(self, total):
        """Single cost line on the configured estimated-landed-cost product.

        ``account_id`` is deliberately left empty: the landed-cost posting
        then falls back to the product's expense account (e.g. a freight
        account), so the estimate is posted as a debit on the goods' stock
        valuation account and a credit on the freight account — the same
        account the actual freight invoice debits later, whose balance
        therefore becomes the estimate-vs-actual variance.
        """
        product = self.company_id.estimated_landed_cost_product_id
        return {
            "product_id": product.id,
            "name": product.name,
            "price_unit": total,
            "split_method": product.split_method_landed_cost or "by_current_cost_price",
            "estimate": True,
        }

    def _prepare_estimated_cost_lines_vals(self, moves):
        """Estimate cost lines for the given receipt moves, each move counting
        only its own quantity."""
        self.ensure_one()
        currency = self.company_id.currency_id
        lc_product = self.company_id.estimated_landed_cost_product_id
        estimates = {
            move: move._get_estimated_landed_cost()
            for move in moves.filtered(
                lambda m, order=self: m.purchase_line_id.order_id == order
            )
        }
        estimates = {
            move: amount
            for move, amount in estimates.items()
            if not currency.is_zero(amount)
        }
        if not estimates:
            return []
        if lc_product:
            return [
                self._prepare_estimated_cost_product_line_vals(
                    currency.round(sum(estimates.values()))
                )
            ]
        return [
            dict(
                self._prepare_estimated_cost_line_vals(
                    move.purchase_line_id, currency.round(amount)
                ),
                estimate_move_id=move.id,
            )
            for move, amount in estimates.items()
        ]

    def _create_picking_with_stock_landed_cost(self, picking):
        # sudo() is needed because only Inventory > Administrator has
        # permissions on stock.landed.cost (see base module)
        landed_cost = super()._create_picking_with_stock_landed_cost(picking).sudo()
        if not landed_cost:
            return landed_cost
        vals_list = self._prepare_estimated_cost_lines_vals(picking.move_ids)
        if vals_list:
            landed_cost.cost_lines = [(0, 0, vals) for vals in vals_list]
        if not landed_cost.cost_lines:
            # if estimate is zero don't keep empty LC
            landed_cost.unlink()
            return self.env["stock.landed.cost"].browse()
        return landed_cost
