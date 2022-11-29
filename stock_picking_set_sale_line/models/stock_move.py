# Copyright 2022 ForgeFlow
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def action_stock_move_sale_line(self):
        return {
            'type': "ir.actions.act_window",
            'name': 'Change the Sale Line related',
            'res_model': 'stock.move.sale.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref("stock_picking_set_sale_line.stock_move_sale_line_wizard_view").id,
            'target': 'new',
            'context': {
                'sale_line_ids': self.picking_id.sale_id.order_line.ids
            }
        }

    # @api.depends('sale_line_id')
    # def update_move_fields(self):
    #     self.write({
    #         "sequence2": self.sale_line_id.sequence2,
    #         "date_expected": self.sale_line_id.commitment_date,
    #         "product_uom_qty": self.sale_line_id.product_uom_qty,
    #     })

    # def write(self, vals):
    #     res = super(StockMove, self).write(vals)
    #     if 'sale_line_id' in vals:
    #         self.sale_line_id
    #     return res
