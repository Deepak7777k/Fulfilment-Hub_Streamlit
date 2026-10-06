def calculate_net_available(inventory):

    inventory = inventory.copy()

    inventory["net_available"] = (
        inventory["available_qty"]
        - inventory["reserved_qty"]
    )

    return inventory


def get_warehouse_stock(
    sku,
    warehouse,
    inventory
):

    stock = inventory[
        (inventory["sku"] == sku)
        &
        (inventory["warehouse"] == warehouse)
    ]

    available = stock["available_qty"].sum()

    reserved = stock["reserved_qty"].sum()

    return available - reserved


def get_transfer_recommendation(
    sku,
    required_qty,
    inventory
):

    main_available = get_warehouse_stock(
        sku,
        "MAIN",
        inventory
    )

    overflow_available = get_warehouse_stock(
        sku,
        "OVERFLOW",
        inventory
    )

    shortage = max(
        0,
        required_qty - main_available
    )

    transferable = min(
        shortage,
        max(0, overflow_available)
    )

    if shortage == 0:

        recommendation = (
            "MAIN STOCK AVAILABLE"
        )

    elif transferable >= shortage:

        recommendation = (
            f"TRANSFER {transferable} UNITS "
            f"FROM OVERFLOW"
        )

    elif transferable > 0:

        remaining_shortage = (
            shortage - transferable
        )

        recommendation = (
            f"PARTIAL TRANSFER: "
            f"{transferable} UNITS. "
            f"REMAINING SHORTAGE: "
            f"{remaining_shortage}"
        )

    else:

        recommendation = (
            "STOCK UNAVAILABLE"
        )

    return {
        "main_available": main_available,
        "overflow_available": overflow_available,
        "shortage": shortage,
        "transferable": transferable,
        "recommendation": recommendation
    }


def get_inventory_shortages(
    orders,
    inventory
):

    shortages = []

    for _, order in orders.iterrows():

        sku = order["sku"]

        required_qty = order["quantity"]

        main_available = get_warehouse_stock(
            sku,
            "MAIN",
            inventory
        )

        if required_qty > main_available:

            overflow_available = (
                get_warehouse_stock(
                    sku,
                    "OVERFLOW",
                    inventory
                )
            )

            shortages.append({
                "order_id": order["order_id"],
                "sku": sku,
                "required_qty": required_qty,
                "main_available": main_available,
                "overflow_available": overflow_available,
                "shortage": (
                    required_qty
                    - main_available
                )
            })

    return shortages


def get_main_inventory(inventory):

    return inventory[
        inventory["warehouse"] == "MAIN"
    ].copy()


def get_overflow_inventory(inventory):

    return inventory[
        inventory["warehouse"] == "OVERFLOW"
    ].copy()


def get_transfer_opportunities(
    orders,
    inventory
):

    opportunities = []

    for _, order in orders.iterrows():

        sku = order["sku"]

        required_qty = order["quantity"]

        result = get_transfer_recommendation(
            sku,
            required_qty,
            inventory
        )

        if (
            result["shortage"] > 0
            and result["transferable"] > 0
        ):

            opportunities.append({
                "order_id": order["order_id"],
                "sku": sku,
                "required_qty": required_qty,
                "main_available": result[
                    "main_available"
                ],
                "overflow_available": result[
                    "overflow_available"
                ],
                "shortage": result[
                    "shortage"
                ],
                "transfer_qty": result[
                    "transferable"
                ],
                "recommendation": result[
                    "recommendation"
                ]
            })

    return opportunities