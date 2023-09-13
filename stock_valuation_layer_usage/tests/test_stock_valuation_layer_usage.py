# 2020 Copyright ForgeFlow, S.L. (https://www.forgeflow.com)
# @author Jordi Ballester <jordi.ballester@forgeflow.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import SavepointCase


class TestStockValuationLayerUsage(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestStockValuationLayerUsage, cls).setUpClass()
        # Get required Model
        cls.product_model = cls.env["product.product"]
        cls.template_model = cls.env["product.template"]
        cls.product_ctg_model = cls.env["product.category"]
        cls.account_model = cls.env["account.account"]
        cls.quant_model = cls.env["stock.quant"]
        cls.layer_model = cls.env["stock.valuation.layer"]
        cls.stock_location_model = cls.env["stock.location"]
        cls.res_users_model = cls.env["res.users"]
        cls.account_move_model = cls.env["account.move"]
        cls.aml_model = cls.env["account.move.line"]
        cls.journal_model = cls.env["account.journal"]
        # Get required Model data
        cls.product_uom = cls.env.ref("uom.product_uom_unit")
        cls.company = cls.env.ref("base.main_company")
        cls.stock_picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.stock_picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.stock_location_id = cls.env.ref("stock.stock_location_stock")
        cls.stock_location_customer_id = cls.env.ref("stock.stock_location_customers")
        cls.stock_location_supplier_id = cls.env.ref("stock.stock_location_suppliers")
        # Account types
        expense_type = cls.env.ref("account.data_account_type_expenses")
        equity_type = cls.env.ref("account.data_account_type_equity")
        asset_type = cls.env.ref("account.data_account_type_fixed_assets")
        # Create account for Goods Received Not Invoiced
        name = "Goods Received Not Invoiced"
        code = "grni"
        acc_type = equity_type
        cls.account_grni = cls._create_account(acc_type, name, code, cls.company)
        # Create account for Cost of Goods Sold
        name = "Cost of Goods Sold"
        code = "cogs"
        acc_type = expense_type
        cls.account_cogs = cls._create_account(acc_type, name, code, cls.company)
        # Create account for Goods Delivered Not Invoiced
        name = "Goods Delivered Not Invoiced"
        code = "gdni"
        acc_type = expense_type
        cls.account_gdni = cls._create_account(acc_type, name, code, cls.company)
        # Create account for Inventory
        name = "Inventory"
        code = "inventory"
        acc_type = asset_type
        cls.account_inventory = cls._create_account(acc_type, name, code, cls.company)

        cls.stock_journal = cls.env["account.journal"].create(
            {"name": "Stock journal", "type": "general", "code": "STK00"}
        )
        # Create product category
        cls.product_ctg = cls._create_product_category()

        # Create partners
        cls.supplier = cls.env["res.partner"].create({"name": "Test supplier"})
        cls.customer = cls.env["res.partner"].create({"name": "Test customer"})

        # Create a Product with real cost
        standard_price = 10.0
        list_price = 20.0
        cls.product = cls._create_product(standard_price, False, list_price)

        # Create a vendor
        cls.vendor_partner = cls.env["res.partner"].create({"name": "dropship vendor"})

    @classmethod
    def _create_user(cls, login, groups, company):
        """Create a user."""
        group_ids = [group.id for group in groups]
        user = cls.res_users_model.with_context({"no_reset_password": True}).create(
            {
                "name": "Test User",
                "login": login,
                "password": "demo",
                "email": "test@yourcompany.com",
                "company_id": company.id,
                "company_ids": [(4, company.id)],
                "groups_id": [(6, 0, group_ids)],
            }
        )
        return user

    @classmethod
    def _create_account(cls, acc_type, name, code, company):
        """Create an account."""
        account = cls.account_model.create(
            {
                "name": name,
                "code": code,
                "user_type_id": acc_type.id,
                "company_id": company.id,
            }
        )
        return account

    @classmethod
    def _create_product_category(cls):
        product_ctg = cls.product_ctg_model.create(
            {
                "name": "test_product_ctg",
                "property_stock_valuation_account_id": cls.account_inventory.id,
                "property_stock_account_input_categ_id": cls.account_grni.id,
                "property_account_expense_categ_id": cls.account_cogs.id,
                "property_stock_account_output_categ_id": cls.account_gdni.id,
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
                "property_stock_journal": cls.stock_journal.id,
            }
        )
        return product_ctg

    @classmethod
    def _create_product(cls, standard_price, template, list_price):
        """Create a Product variant."""
        if not template:
            template = cls.template_model.create(
                {
                    "name": "test_product",
                    "categ_id": cls.product_ctg.id,
                    "type": "product",
                    "standard_price": standard_price,
                    "valuation": "real_time",
                    "invoice_policy": "delivery",
                }
            )
            return template.product_variant_ids[0]
        product = cls.product_model.create(
            {"product_tmpl_id": template.id, "list_price": list_price}
        )
        return product

    def _create_delivery(
        self, product, qty,
    ):
        return self.env["stock.picking"].create(
            {
                "name": self.stock_picking_type_out.sequence_id._next(),
                "partner_id": self.customer.id,
                "picking_type_id": self.stock_picking_type_out.id,
                "location_id": self.stock_location_id.id,
                "location_dest_id": self.stock_location_customer_id.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": qty,
                            "location_id": self.stock_location_id.id,
                            "location_dest_id": self.stock_location_customer_id.id,
                            "procure_method": "make_to_stock",
                        },
                    )
                ],
            }
        )

    def _create_drophip_picking(
        self, product, qty,
    ):
        return self.env["stock.picking"].create(
            {
                "name": self.stock_picking_type_out.sequence_id._next(),
                "partner_id": self.customer.id,
                "picking_type_id": self.stock_picking_type_out.id,
                "location_id": self.stock_location_supplier_id.id,
                "location_dest_id": self.stock_location_customer_id.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": qty,
                            "location_id": self.stock_location_supplier_id.id,
                            "location_dest_id": self.stock_location_customer_id.id,
                        },
                    )
                ],
            }
        )

    def _create_receipt(self, product, qty, move_dest_id=None):
        move_dest_id = [(4, move_dest_id)] if move_dest_id else False
        return self.env["stock.picking"].create(
            {
                "name": self.stock_picking_type_in.sequence_id._next(),
                "partner_id": self.vendor_partner.id,
                "picking_type_id": self.stock_picking_type_in.id,
                "location_id": self.stock_location_supplier_id.id,
                "location_dest_id": self.stock_location_id.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": qty,
                            "price_unit": 10.0,
                            "move_dest_ids": move_dest_id,
                            "location_id": self.stock_location_supplier_id.id,
                            "location_dest_id": self.stock_location_id.id,
                            "procure_method": "make_to_stock",
                        },
                    )
                ],
            }
        )

    def _do_picking(self, picking, date, qty):
        """Do picking with only one move on the given date."""
        picking.action_confirm()
        picking.action_assign()
        picking.move_lines.quantity_done = qty
        res = picking.button_validate()
        if res:
            backorder_wiz_id = res["res_id"]
            backorder_wiz = self.env["stock.backorder.confirmation"].browse(
                [backorder_wiz_id]
            )
            backorder_wiz.process()
        return True
