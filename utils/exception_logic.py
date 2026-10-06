import pandas as pd


def get_open_exceptions(exceptions):
    """
    Return only currently open exceptions.
    """

    if exceptions is None or exceptions.empty:
        return pd.DataFrame()

    if "status" not in exceptions.columns:
        return exceptions.copy()

    return exceptions[
        exceptions["status"]
        .astype(str)
        .str.upper()
        == "OPEN"
    ].copy()


def get_exception_metrics(exceptions):
    """
    Return basic exception metrics.
    """

    open_exceptions = get_open_exceptions(exceptions)

    if open_exceptions.empty:
        return {
            "open": 0,
            "critical": 0,
            "high": 0
        }

    severity = (
        open_exceptions["severity"]
        .astype(str)
        .str.upper()
    )

    return {
        "open": len(open_exceptions),
        "critical": int(
            (severity == "CRITICAL").sum()
        ),
        "high": int(
            (severity == "HIGH").sum()
        )
    }


def filter_exceptions_by_severity(
    exceptions,
    severity
):
    """
    Filter exceptions by severity.
    """

    if exceptions is None or exceptions.empty:
        return pd.DataFrame()

    if "severity" not in exceptions.columns:
        return exceptions.copy()

    return exceptions[
        exceptions["severity"]
        .astype(str)
        .str.upper()
        == str(severity).upper()
    ].copy()


def get_critical_exceptions(exceptions):
    """
    Return critical exceptions.
    """

    return filter_exceptions_by_severity(
        exceptions,
        "CRITICAL"
    )


def get_exceptions_by_type(
    exceptions,
    exception_type
):
    """
    Return exceptions of a specific type.
    """

    if exceptions is None or exceptions.empty:
        return pd.DataFrame()

    if "type" not in exceptions.columns:
        return exceptions.copy()

    return exceptions[
        exceptions["type"]
        .astype(str)
        .str.upper()
        == str(exception_type).upper()
    ].copy()


def get_exception_summary(exceptions):
    """
    Return a summary of exceptions by type.
    """

    if exceptions is None or exceptions.empty:
        return pd.DataFrame()

    if "type" not in exceptions.columns:
        return pd.DataFrame()

    return (
        exceptions["type"]
        .astype(str)
        .str.upper()
        .value_counts()
        .reset_index()
        .rename(
            columns={
                "type": "exception_type",
                "count": "count"
            }
        )
    )


def get_exception_action(row):
    """
    Return recommended operational action.

    This function accepts either:
    - a complete Pandas row/Series
    - a single exception type string
    """

    actions = {
        "INVENTORY_SHORTAGE": (
            "Check main warehouse stock and initiate "
            "overflow transfer."
        ),

        "WRONG_VARIANT": (
            "Stop shipment and verify the product variant "
            "before dispatch."
        ),

        "WRONG_PRODUCT": (
            "Stop shipment and recheck the picked SKU "
            "against the order."
        ),

        "COURIER_DELAY": (
            "Contact courier and arrange an alternate "
            "pickup if required."
        ),

        "MISPLACED_BOX": (
            "Locate the box and verify its staging location."
        ),

        "INVENTORY_MISMATCH": (
            "Perform a physical count and reconcile "
            "inventory records."
        )
    }

    # If a complete dataframe row is passed
    if isinstance(row, pd.Series):

        exception_type = row.get(
            "type",
            ""
        )

    # If a dictionary is passed
    elif isinstance(row, dict):

        exception_type = row.get(
            "type",
            ""
        )

    # If a single string is passed
    else:

        exception_type = row

    exception_type = str(
        exception_type
    ).strip().upper()

    return actions.get(
        exception_type,
        "Review the exception and determine the required action."
    )