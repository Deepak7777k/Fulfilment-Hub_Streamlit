import pandas as pd


def get_status_column(shipments):
    """
    Find the actual shipment status column.
    """

    if "pickup_status" in shipments.columns:
        return "pickup_status"

    if "status" in shipments.columns:
        return "status"

    if "shipment_status" in shipments.columns:
        return "shipment_status"

    return None


def get_pickup_time_column(shipments):
    """
    Find the actual pickup time column.
    """

    if "pickup_time" in shipments.columns:
        return "pickup_time"

    if "scheduled_pickup" in shipments.columns:
        return "scheduled_pickup"

    return None


def calculate_pickup_status(
    pickup_time,
    shipment_status,
    current_time=None
):
    """
    Calculate courier pickup risk.
    """

    if current_time is None:
        current_time = pd.Timestamp.now()

    pickup_time = pd.to_datetime(
        pickup_time,
        errors="coerce"
    )

    if pd.isna(pickup_time):
        return "UNKNOWN"

    shipment_status = str(
        shipment_status
    ).strip().upper()

    if shipment_status == "PICKED_UP":
        return "COMPLETED"

    time_difference = pickup_time - current_time

    if time_difference.total_seconds() < 0:
        return "OVERDUE"

    if time_difference.total_seconds() <= 60 * 60:
        return "DUE SOON"

    return "SCHEDULED"


def add_pickup_risk(shipments):

    shipments = shipments.copy()

    status_column = get_status_column(shipments)
    pickup_time_column = get_pickup_time_column(shipments)

    if pickup_time_column is None:
        shipments["pickup_risk"] = "UNKNOWN"
        return shipments

    if status_column is None:
        shipments["pickup_risk"] = "UNKNOWN"
        return shipments

    shipments[pickup_time_column] = pd.to_datetime(
        shipments[pickup_time_column],
        errors="coerce"
    )

    current_time = pd.Timestamp.now()

    shipments["pickup_risk"] = shipments.apply(
        lambda row: calculate_pickup_status(
            row[pickup_time_column],
            row[status_column],
            current_time
        ),
        axis=1
    )

    return shipments


def get_overdue_pickups(shipments):

    if "pickup_risk" not in shipments.columns:
        shipments = add_pickup_risk(shipments)

    return shipments[
        shipments["pickup_risk"] == "OVERDUE"
    ].copy()


def get_due_soon_pickups(shipments):

    if "pickup_risk" not in shipments.columns:
        shipments = add_pickup_risk(shipments)

    return shipments[
        shipments["pickup_risk"] == "DUE SOON"
    ].copy()


def get_shipment_metrics(shipments):

    if "pickup_risk" not in shipments.columns:
        shipments = add_pickup_risk(shipments)

    status_column = get_status_column(shipments)

    if status_column is None:
        return {
            "scheduled": 0,
            "ready": 0,
            "picked_up": 0,
            "pickup_overdue": int(
                (
                    shipments["pickup_risk"]
                    == "OVERDUE"
                ).sum()
            )
        }

    status = (
        shipments[status_column]
        .astype(str)
        .str.upper()
    )

    return {
        "scheduled": int(
            (status == "SCHEDULED").sum()
        ),

        "ready": int(
            (status == "READY").sum()
        ),

        "picked_up": int(
            (status == "PICKED_UP").sum()
        ),

        "pickup_overdue": int(
            (
                shipments["pickup_risk"]
                == "OVERDUE"
            ).sum()
        )
    }


def get_pickup_action(row):

    pickup_risk = str(
        row.get("pickup_risk", "")
    ).upper()

    status = str(
        row.get(
            "pickup_status",
            row.get(
                "status",
                row.get(
                    "shipment_status",
                    ""
                )
            )
        )
    ).upper()

    if pickup_risk == "OVERDUE":
        return (
            "Contact courier immediately and arrange "
            "pickup or alternate courier."
        )

    if pickup_risk == "DUE SOON":
        return (
            "Confirm package is ready and coordinate "
            "with courier."
        )

    if status == "READY":
        return (
            "Keep package staged and ready for courier pickup."
        )

    if status == "PICKED_UP":
        return "No action required."

    return "Monitor shipment."