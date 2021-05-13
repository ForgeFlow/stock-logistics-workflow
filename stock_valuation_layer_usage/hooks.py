# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.base.models.ir_model import query_insert

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """
    The objective of this hook is to update the field purchase_state in
    existing purchase request lines
    """
    fill_svl_usage_dropshipments(cr)


def _prepare_svl_usage_vals(index, move, quantity, value):
    return {
        "create_uid": move["write_uid"],
        "create_date": move["date"],
        "write_uid": move["write_uid"],
        "write_date": move["date"],
        "stock_valuation_layer_id": index,
        "stock_move_id": move["id"],
        "quantity": quantity,
        "value": value,
        "company_id": move["company_id"],
        "product_id": move["product_id"],
    }


def fill_svl_usage_dropshipments(cr):
    # pylint: disable=W0105
    _logger.info("Filling usages on dropshipments")
    """After generate_stock_valuation_layer dropship layers are not linked"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    svl_usage_vals_list = []
    openupgrade.logged_query(
        env.cr,
        """
        SELECT count(*) as layer_no, sm.id as id, sm.company_id, sm.product_id,
            sm.date, sm.create_uid, sm.create_date, sm.write_uid, sm.write_date
        FROM stock_move sm
        LEFT JOIN stock_location sl ON sl.id = sm.location_id
        LEFT JOIN stock_location sld ON sld.id = sm.location_dest_id
        INNER JOIN stock_valuation_layer svl ON svl.stock_move_id = sm.id
        WHERE (sl.usage = 'supplier' AND sld.usage = 'customer')
            OR (sl.usage = 'customer' AND sld.usage = 'supplier')
        GROUP BY sm.id
        HAVING count(*) = 2
        """,
    )
    for move in env.cr.dictfetchall():
        move_rec = env["stock.move"].browse(move["id"])
        incoming = move_rec.stock_valuation_layer_ids.filtered(
            lambda svl: svl.quantity > 0
        )
        outgoing = move_rec.stock_valuation_layer_ids.filtered(
            lambda svl: svl.quantity < 0
        )
        if (
            incoming
            and outgoing
            and incoming.quantity == -outgoing.quantity
            and not incoming.usage_ids
        ):
            svl_usage_vals = _prepare_svl_usage_vals(
                incoming.id, move, incoming.quantity, incoming.value
            )
            svl_usage_vals_list.append(svl_usage_vals)
    if svl_usage_vals_list:
        svl_usage_vals_list = sorted(
            svl_usage_vals_list, key=lambda k: (k["create_date"])
        )
        # pylint: disable=W0105
        _logger.info(
            "To create {} svl usage dropship records".format(len(svl_usage_vals_list))
        )
        query_insert(env.cr, "stock_valuation_layer_usage", svl_usage_vals_list)
