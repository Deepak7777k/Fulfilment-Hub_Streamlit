import pandas as pd


# =========================================================
# SLA LOGIC
# =========================================================

def calculate_sla_status(deadline, current_time):
    """
    Determine the SLA status of an order.
    """

    minutes_remaining = (
        deadline - current_time
    ).total_seconds() / 60

    if minutes_remaining < 0:
        return "OVERDUE"

    elif minutes_remaining <= 60:
        return "DUE SOON"

    else:
        return "ON TRACK"


# =========================================================
# RISK LOGIC
# =========================================================

def determine_risk(priority, sla_status):
    """
    Determine operational risk.
    """

    if (
        priority == "HIGH"
        and sla_status == "OVERDUE"
    ):
        return "CRITICAL"

    if sla_status == "OVERDUE":
        return "HIGH"

    if (
        priority == "HIGH"
        and sla_status == "DUE SOON"
    ):
        return "HIGH"

    if sla_status == "DUE SOON":
        return "MEDIUM"

    return "LOW"


# =========================================================
# ADD SLA + RISK TO ORDERS
# =========================================================

def add_sla_and_risk(orders):

    orders = orders.copy()

    current_time = pd.Timestamp.now().floor("min")

    orders["sla_status"] = orders.apply(
        lambda row: calculate_sla_status(
            row["deadline"],
            current_time
        ),
        axis=1
    )

    orders["risk"] = orders.apply(
        lambda row: determine_risk(
            row["priority"],
            row["sla_status"]
        ),
        axis=1
    )

    return orders


# =========================================================
# URGENT ORDERS
# =========================================================

def get_urgent_orders(orders):

    urgent_orders = orders[
        orders["risk"].isin(
            ["CRITICAL", "HIGH"]
        )
    ].copy()

    risk_order = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    urgent_orders["risk_rank"] = (
        urgent_orders["risk"].map(
            risk_order
        )
    )

    urgent_orders = urgent_orders.sort_values(
        ["risk_rank", "deadline"]
    )

    return urgent_orders.drop(
        columns=["risk_rank"]
    )


# =========================================================
# ORDER METRICS
# =========================================================

def get_order_metrics(orders):

    return {
        "total_orders": len(orders),

        "priority_orders": len(
            orders[
                orders["priority"] == "HIGH"
            ]
        ),

        "at_risk": len(
            orders[
                orders["sla_status"].isin(
                    [
                        "OVERDUE",
                        "DUE SOON"
                    ]
                )
            ]
        ),

        "ready_to_ship": len(
            orders[
                orders["status"] == "STAGED"
            ]
        )
    }


# =========================================================
# CRITICAL ORDERS
# =========================================================

def get_critical_orders(orders):

    return orders[
        orders["risk"] == "CRITICAL"
    ].copy()


# =========================================================
# DUE SOON ORDERS
# =========================================================

def get_due_soon_orders(orders):

    return orders[
        orders["sla_status"] == "DUE SOON"
    ].copy()


# =========================================================
# ORDER DETAIL
# =========================================================

def get_order_details(
    order_id,
    orders,
    inventory,
    exceptions,
    shipments
):
    """
    Build a complete operational view
    for one selected order.
    """

    order_rows = orders[
        orders["order_id"] == order_id
    ]

    if order_rows.empty:
        return None

    order = order_rows.iloc[0]

    # -----------------------------------------------------
    # Product / Inventory
    # -----------------------------------------------------

    sku = order["sku"]

    required_qty = order["quantity"]

    main_stock = inventory[
        (inventory["sku"] == sku)
        &
        (inventory["warehouse"] == "MAIN")
    ]

    overflow_stock = inventory[
        (inventory["sku"] == sku)
        &
        (inventory["warehouse"] == "OVERFLOW")
    ]

    main_available = (
        main_stock["available_qty"].sum()
        -
        main_stock["reserved_qty"].sum()
    )

    overflow_available = (
        overflow_stock["available_qty"].sum()
        -
        overflow_stock["reserved_qty"].sum()
    )

    shortage = max(
        0,
        required_qty - main_available
    )

    transfer_qty = min(
        shortage,
        max(0, overflow_available)
    )

    # -----------------------------------------------------
    # Exceptions
    # -----------------------------------------------------

    order_exceptions = exceptions[
        exceptions["order_id"] == order_id
    ].copy()

    # -----------------------------------------------------
    # Shipment
    # -----------------------------------------------------

    order_shipments = shipments[
        shipments["order_id"] == order_id
    ].copy()

    return {
        "order": order,
        "sku": sku,
        "required_qty": required_qty,
        "main_available": main_available,
        "overflow_available": overflow_available,
        "shortage": shortage,
        "transfer_qty": transfer_qty,
        "exceptions": order_exceptions,
        "shipments": order_shipments
    }


# =========================================================
# RECOMMENDED ACTION
# =========================================================

def get_recommended_action(order_details):
    """
    Return the recommended operational action for an order.
    
    The function accepts the dictionary returned by
    get_order_details().
    """

    if order_details is None:
        return "Review order details and determine the required action."

    # Expected structure from get_order_details()
    if isinstance(order_details, dict):

        order = order_details.get("order")

        if order is None:
            return "Review order details and determine the required action."

        sku = order_details.get("sku")
        required_qty = order_details.get("required_qty", 0)
        main_available = order_details.get("main_available", 0)
        overflow_available = order_details.get(
            "overflow_available",
            0
        )

        shortage = order_details.get(
            "shortage",
            max(required_qty - main_available, 0)
        )

        transfer_qty = order_details.get(
            "transfer_qty",
            min(shortage, overflow_available)
        )

    else:
        return "Review order details and determine the required action."

    priority = str(
        order.get("priority", "")
    ).upper()

    status = str(
        order.get("status", "")
    ).upper()

    sla_status = str(
        order.get("sla_status", "")
    ).upper()

    risk = str(
        order.get("risk", "")
    ).upper()

    # --------------------------------------------------------
    # 1. Critical SLA
    # --------------------------------------------------------

    if sla_status == "OVERDUE" and priority == "HIGH":
        return (
            "Escalate immediately. Priority order is overdue "
            "and requires urgent intervention."
        )

    # --------------------------------------------------------
    # 2. Inventory shortage with overflow stock
    # --------------------------------------------------------

    if shortage > 0 and transfer_qty > 0:

        if transfer_qty >= shortage:
            return (
                f"Transfer {int(transfer_qty)} unit(s) of "
                f"{sku} from overflow to the main warehouse."
            )

        return (
            f"Transfer {int(transfer_qty)} unit(s) of "
            f"{sku} from overflow. Remaining shortage: "
            f"{int(shortage - transfer_qty)} unit(s)."
        )

    # --------------------------------------------------------
    # 3. No inventory available
    # --------------------------------------------------------

    if shortage > 0 and overflow_available <= 0:
        return (
            "Inventory is insufficient. Escalate replenishment "
            "or consider an alternative fulfilment location."
        )

    # --------------------------------------------------------
    # 4. Critical/high exception
    # --------------------------------------------------------

    exceptions = order_details.get(
        "exceptions",
        []
    )

    if exceptions is not None:

        if hasattr(exceptions, "empty"):

            if not exceptions.empty:

                severities = (
                    exceptions["severity"]
                    .astype(str)
                    .str.upper()
                    .tolist()
                    if "severity" in exceptions.columns
                    else []
                )

                if "CRITICAL" in severities:
                    return (
                        "Stop fulfilment and resolve the critical "
                        "exception before proceeding."
                    )

                if "HIGH" in severities:
                    return (
                        "Resolve the high-severity exception "
                        "before proceeding."
                    )

        elif isinstance(exceptions, list):

            for exception in exceptions:

                if isinstance(exception, dict):

                    severity = str(
                        exception.get("severity", "")
                    ).upper()

                    if severity == "CRITICAL":
                        return (
                            "Stop fulfilment and resolve the "
                            "critical exception before proceeding."
                        )

                    if severity == "HIGH":
                        return (
                            "Resolve the high-severity exception "
                            "before proceeding."
                        )

    # --------------------------------------------------------
    # 5. High priority due soon
    # --------------------------------------------------------

    if priority == "HIGH" and sla_status == "DUE SOON":
        return (
            "Prioritize this order immediately to meet "
            "the SLA deadline."
        )

    # --------------------------------------------------------
    # 6. Status-based actions
    # --------------------------------------------------------

    if status == "PACKING":
        return (
            "Complete packing and move the order to staging."
        )

    if status == "STAGED":
        return (
            "Order is ready to ship. Confirm courier pickup."
        )

    if status == "PICKING":
        return (
            "Complete picking and verify SKU and quantity."
        )

    if status == "PROCESSING":
        return (
            "Complete order processing and move to picking."
        )

    if status == "RECEIVED":
        return (
            "Process the order and move it to the picking queue."
        )

    # --------------------------------------------------------
    # 7. Risk fallback
    # --------------------------------------------------------

    if risk == "CRITICAL":
        return (
            "Escalate immediately and review the order."
        )

    if risk == "HIGH":
        return (
            "Prioritize this order and monitor progress closely."
        )

    return "Monitor order progress."