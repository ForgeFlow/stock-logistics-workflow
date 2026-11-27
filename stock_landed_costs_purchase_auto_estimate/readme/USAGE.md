1.  Follow instructions in the module stock_landed_costs_purchase_auto
2.  The estimated landed cost related to the purchase order will be added
    based on the indictect cost percentage of the supplierinfo
3.  The estimate is recomputed when the receipt is validated, from the
    quantities actually received: a partial receipt is charged for what it
    received, and its backorder gets its own estimate for the rest. Each
    received move carries the estimate of its own vendor percentage. Cost
    lines added manually to the landed cost are kept.
