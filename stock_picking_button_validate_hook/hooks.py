# Copyright 2020 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo.addons.stock.models.stock_picking import Picking
from odoo import _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


def post_load_hook():

    def button_validate_new(self):
        if not hasattr(self, '_button_validate_get_no_quantities_done'):
            return self._action_done_original()

        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))
        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        # START OF PATCH #
        no_quantities_done = self._button_validate_get_no_quantities_done()
        no_reserved_quantities = \
            self._validate_get_no_reserved_quantities()
        # END OF PATCH #
        if no_reserved_quantities and no_quantities_done and not self.picking_type_id.code == 'incoming':
            raise UserError(_(
                'You cannot validate a transfer if no quantites '
                'are reserved nor done. To force the transfer, switch '
                'in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(
                        line.qty_done, 0,
                        precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_(
                            'You need to supply a Lot/Serial number f'
                            'or product %s.') % product.display_name)

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create(
                {'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        if self._get_overprocessed_stock_moves() and not self._context.get(
                'skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create(
                {'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        return

    if not hasattr(Picking, 'button_validate_original'):
        Picking.button_validate_original = Picking.button_validate
    Picking.button_validate = button_validate_new
