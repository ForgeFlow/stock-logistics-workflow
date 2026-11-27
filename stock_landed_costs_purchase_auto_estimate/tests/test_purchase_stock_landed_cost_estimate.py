from .common import TestPurchaseStockLandedCostEstimateBase


class TestPurchaseStockLandedCostEstimate(TestPurchaseStockLandedCostEstimateBase):
    def test_cost_lines_calculation(self):
        self.order.button_confirm()
        landed_costs = self.order.landed_cost_ids
        # only one cost lines and the cost lines are 10% of the purchase price
        self.assertEqual(len(landed_costs.cost_lines), 1)
        self.assertEqual(landed_costs.cost_lines.price_unit, 1)
        # the state is draft unless the pickign is validated
        self.assertEqual(landed_costs.state, "draft")
        self._action_picking_validate(self.order.picking_ids)
        self.assertEqual(landed_costs.state, "done")
        # the stock move cost is the total
        self.assertEqual(
            self.order.picking_ids.move_ids.value,
            landed_costs.cost_lines.price_unit
            + self.order.order_line[0].price_subtotal,
        )

    def test_cost_lines_cancelation(self):
        self.order.button_confirm()
        self.order.picking_ids.action_cancel()
        landed_costs = self.order.landed_cost_ids
        self.assertEqual(landed_costs.state, "cancel")

    def test_no_cost_lines_when_no_supplierinfo(self):
        supplier2 = self.env["res.partner"].create({"name": "Supplier 2"})
        self.order.partner_id = supplier2
        self.order.button_confirm()
        landed_costs = self.order.landed_cost_ids
        self.assertEqual(len(landed_costs.cost_lines), 0)

    def test_partial_receipt_estimates_received_quantity(self):
        self.product_storable.is_storable = True
        self.order.order_line.product_qty = 10
        self.order.button_confirm()
        picking = self.order.picking_ids
        picking.action_assign()
        picking.move_ids.quantity = 4
        self._action_picking_validate(picking)
        backorder = self.order.picking_ids - picking
        first_cost = picking.stock_landed_costs_ids
        self.assertEqual(first_cost.state, "done")
        # 10% of 4 units at 10.00
        self.assertAlmostEqual(first_cost.amount_total, 4.0)
        self.assertAlmostEqual(picking.move_ids.value, 44.0)
        self._action_picking_validate(backorder)
        second_cost = backorder.stock_landed_costs_ids
        self.assertEqual(second_cost.state, "done")
        self.assertAlmostEqual(second_cost.amount_total, 6.0)
        # the whole order is charged 10% once
        self.assertAlmostEqual(
            sum(self.order.landed_cost_ids.mapped("amount_total")),
            self.order.order_line.price_subtotal * 0.1,
        )

    def test_manual_cost_line_kept_on_validation(self):
        self.product_storable.is_storable = True
        self.order.button_confirm()
        landed_cost = self.order.landed_cost_ids
        freight = self.env["product.product"].create(
            {"name": "Freight (test)", "type": "service", "landed_cost_ok": True}
        )
        landed_cost.cost_lines = [
            (
                0,
                0,
                {
                    "product_id": freight.id,
                    "name": freight.name,
                    "price_unit": 5,
                    "split_method": "equal",
                    "account_id": landed_cost.cost_lines.account_id.id,
                },
            )
        ]
        self._action_picking_validate(self.order.picking_ids)
        self.assertEqual(landed_cost.state, "done")
        self.assertEqual(len(landed_cost.cost_lines), 2)
        self.assertIn(freight, landed_cost.cost_lines.product_id)
        self.assertAlmostEqual(landed_cost.amount_total, 6.0)
