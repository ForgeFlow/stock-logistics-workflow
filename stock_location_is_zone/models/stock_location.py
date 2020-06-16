# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"
    _order = "is_zone desc, complete_name"

    is_zone = fields.Boolean(
        string="Is Zone", help="When locations are listed, the zone will appear first.",
    )
