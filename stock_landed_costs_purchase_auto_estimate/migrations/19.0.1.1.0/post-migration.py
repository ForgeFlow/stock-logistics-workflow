# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    """Flag the cost lines the module created before the flag existed: the
    configured estimate product, or the purchased goods themselves (legacy
    lines), on landed costs created from a purchase order."""
    cr.execute(
        """
        UPDATE stock_landed_cost_lines cl
        SET estimate = TRUE
        FROM stock_landed_cost lc
        JOIN res_company c ON c.id = lc.company_id
        WHERE cl.cost_id = lc.id
            AND lc.purchase_id IS NOT NULL
            AND (
                cl.product_id = c.estimated_landed_cost_product_id
                OR EXISTS (
                    SELECT 1
                    FROM stock_landed_cost_stock_picking_rel rel
                    JOIN stock_move sm ON sm.picking_id = rel.stock_picking_id
                    WHERE rel.stock_landed_cost_id = lc.id
                        AND sm.product_id = cl.product_id
                )
            )
        """,
    )
