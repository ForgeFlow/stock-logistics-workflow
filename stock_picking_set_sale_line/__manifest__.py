# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Picking set Sale Line",
    "version": "13.0.1.0.0",
    "category": "Inventory",
    "summary": "Provides a button on stock pickings's Operations, allowing to change the sale line it refers to.",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-workflow",
    "depends": ["sale_stock"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/stock_move_sale_wizard_view.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
