import streamlit as st
import pandas as pd
import plotly.express as px

from utils.order_logic import (
    add_sla_and_risk,
    get_critical_orders,
    get_order_details,
    get_recommended_action
)

from utils.inventory_logic import (
    calculate_net_available,
    get_transfer_recommendation,
    get_transfer_opportunities
)

from utils.exception_logic import (
    get_open_exceptions,
    get_exception_action
)

from utils.shipment_logic import (
    add_pickup_risk,
    get_overdue_pickups,
    get_due_soon_pickups,
    get_shipment_metrics,
    get_pickup_action
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Fulfilment Hub",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CONSTANTS
# ============================================================

ORDER_STATUSES = [
    "RECEIVED",
    "PROCESSING",
    "PICKING",
    "PACKING",
    "STAGED",
    "SHIPPED",
    "EXCEPTION"
]

PRIORITIES = ["HIGH", "NORMAL"]

RISK_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

SLA_STATUSES = ["OVERDUE", "DUE SOON", "ON TRACK"]


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data():
    products = pd.read_csv("data/products.csv")
    inventory = pd.read_csv("data/inventory.csv")
    orders = pd.read_csv("data/orders.csv")
    shipments = pd.read_csv("data/shipments.csv")
    exceptions = pd.read_csv("data/exceptions.csv")

    # Convert dates
    if "order_date" in orders.columns:
        orders["order_date"] = pd.to_datetime(
            orders["order_date"],
            errors="coerce"
        )

    if "deadline" in orders.columns:
        orders["deadline"] = pd.to_datetime(
            orders["deadline"],
            errors="coerce"
        )

    if "scheduled_pickup" in shipments.columns:
        shipments["scheduled_pickup"] = pd.to_datetime(
            shipments["scheduled_pickup"],
            errors="coerce"
        )

    if "created_at" in exceptions.columns:
        exceptions["created_at"] = pd.to_datetime(
            exceptions["created_at"],
            errors="coerce"
        )

    return (
        products,
        inventory,
        orders,
        shipments,
        exceptions
    )


products, inventory, orders, shipments, exceptions = load_data()


# ============================================================
# BUSINESS LOGIC
# ============================================================

# Add SLA and order risk information
orders = add_sla_and_risk(orders)

# Calculate inventory net availability
inventory = calculate_net_available(inventory)

# Add shipment pickup risk
shipments = add_pickup_risk(shipments)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_number(value):
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value


def get_today_orders():
    if "order_date" not in orders.columns:
        return orders.copy()

    today = pd.Timestamp.now().normalize()

    return orders[
        orders["order_date"].dt.normalize() == today
    ].copy()


def get_open_exception_count():
    if "status" not in exceptions.columns:
        return 0

    return int(
        (exceptions["status"].astype(str).str.upper() == "OPEN").sum()
    )


def get_ready_to_ship_count():
    if "status" not in orders.columns:
        return 0

    return int(
        (
            orders["status"].astype(str).str.upper() == "STAGED"
        ).sum()
    )


def get_priority_count():
    if "priority" not in orders.columns:
        return 0

    return int(
        (
            orders["priority"].astype(str).str.upper() == "HIGH"
        ).sum()
    )


def get_at_risk_count():
    if "risk" not in orders.columns:
        return 0

    return int(
        orders["risk"].astype(str).str.upper().isin(
            ["CRITICAL", "HIGH"]
        ).sum()
    )


def safe_filter(df, column, value):
    if column not in df.columns:
        return df.copy()

    return df[
        df[column].astype(str).str.upper() == str(value).upper()
    ].copy()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📦 Fulfilment Hub")
st.sidebar.caption("Operations Control Center")

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    [
        "Dashboard",
        "Orders",
        "Inventory",
        "Exceptions",
        "Shipments"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "Order visibility • SLA monitoring • Inventory • "
    "Exceptions • Shipping"
)


# ============================================================
# HEADER
# ============================================================

st.title("Fulfilment Hub")
st.caption(
    "Operations Control Center | "
    "Order visibility • SLA monitoring • Inventory • "
    "Exceptions • Shipping"
)


# ============================================================
# DASHBOARD
# ============================================================

def show_dashboard():

    st.header("Operations Dashboard")

    today_orders = get_today_orders()

    total_orders = len(today_orders)

    # If generated dummy data does not contain today's orders,
    # use the full dataset so the dashboard remains useful.
    if total_orders == 0:
        dashboard_orders = orders.copy()
        total_orders = len(dashboard_orders)
    else:
        dashboard_orders = today_orders

    priority_orders = get_priority_count()
    at_risk = get_at_risk_count()
    open_exceptions = get_open_exception_count()
    ready_to_ship = get_ready_to_ship_count()

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Today's Orders",
            format_number(total_orders)
        )

    with col2:
        st.metric(
            "Priority Orders",
            format_number(priority_orders)
        )

    with col3:
        st.metric(
            "At Risk",
            format_number(at_risk)
        )

    with col4:
        st.metric(
            "Open Exceptions",
            format_number(open_exceptions)
        )

    with col5:
        st.metric(
            "Ready to Ship",
            format_number(ready_to_ship)
        )

    st.info(
        "Use the Action Center below to identify what needs "
        "attention first."
    )

    st.divider()

    # --------------------------------------------------------
    # ACTION CENTER
    # --------------------------------------------------------

    st.subheader("🚨 Action Center")

    action_col1, action_col2 = st.columns(2)

    # Critical orders
    with action_col1:

        st.markdown("### Critical Orders")

        critical_orders = get_critical_orders(orders)

        if critical_orders is not None and not critical_orders.empty:

            display_columns = [
                col for col in [
                    "order_id",
                    "priority",
                    "status",
                    "sla_status",
                    "risk"
                ]
                if col in critical_orders.columns
            ]

            st.dataframe(
                critical_orders[display_columns].head(8),
                width="stretch",
                hide_index=True
            )

        else:
            st.success("No critical orders.")

    # Transfer opportunities
    with action_col2:

        st.markdown("### Inventory Transfers")

        transfer_opportunities = get_transfer_opportunities(
            orders,
            inventory
        )

        if transfer_opportunities:

            transfer_df = pd.DataFrame(
                transfer_opportunities
            )

            if not transfer_df.empty:

                display_columns = [
                    col for col in [
                        "order_id",
                        "sku",
                        "main_available",
                        "overflow_available",
                        "shortage",
                        "transfer_qty"
                    ]
                    if col in transfer_df.columns
                ]

                st.dataframe(
                    transfer_df[display_columns].head(8),
                    width="stretch",
                    hide_index=True
                )

            else:
                st.success(
                    "No inventory transfer opportunities."
                )
        else:
            st.success(
                "No inventory transfer opportunities."
            )

    # Open exceptions
    st.markdown("### Open Exceptions")

    open_exceptions_df = get_open_exceptions(exceptions)

    if (
        open_exceptions_df is not None
        and not open_exceptions_df.empty
    ):

        exception_display = open_exceptions_df.copy()

        if "recommended_action" not in exception_display.columns:
            exception_display["recommended_action"] = (
                exception_display.apply(
                    get_exception_action,
                    axis=1
                )
            )

        display_columns = [
            col for col in [
                "exception_id",
                "order_id",
                "type",
                "severity",
                "status",
                "recommended_action"
            ]
            if col in exception_display.columns
        ]

        st.dataframe(
            exception_display[display_columns].head(8),
            width="stretch",
            hide_index=True
        )

    else:
        st.success("No open exceptions.")

    st.divider()

    # --------------------------------------------------------
    # ORDER PIPELINE
    # --------------------------------------------------------

    st.subheader("Order Pipeline")

    if "status" in orders.columns:

        pipeline = (
            orders["status"]
            .astype(str)
            .str.upper()
            .value_counts()
            .reindex(
                ORDER_STATUSES,
                fill_value=0
            )
            .reset_index()
        )

        pipeline.columns = ["status", "orders"]

        fig = px.bar(
            pipeline,
            x="status",
            y="orders",
            text="orders",
            title="Orders by Current Status"
        )

        fig.update_layout(
            xaxis_title="Order Status",
            yaxis_title="Number of Orders"
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    # --------------------------------------------------------
    # URGENT ORDERS
    # --------------------------------------------------------

    st.subheader("Urgent Orders")

    urgent_orders = orders[
        orders["risk"].astype(str).str.upper().isin(
            ["CRITICAL", "HIGH"]
        )
    ].copy()

    if not urgent_orders.empty:

        display_columns = [
            col for col in [
                "order_id",
                "priority",
                "status",
                "deadline",
                "sla_status",
                "risk"
            ]
            if col in urgent_orders.columns
        ]

        st.dataframe(
            urgent_orders[
                display_columns
            ].sort_values(
                by="deadline",
                ascending=True
            ).head(15),
            width="stretch",
            hide_index=True
        )

    else:
        st.success("No urgent orders currently require attention.")


# ============================================================
# ORDERS PAGE
# ============================================================

def show_orders():

    st.header("Order Management")

    st.caption(
        "Monitor order status, SLA risk, inventory availability "
        "and recommended operational actions."
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        priority_filter = st.multiselect(
            "Priority",
            PRIORITIES,
            default=[]
        )

    with col2:
        status_filter = st.multiselect(
            "Status",
            ORDER_STATUSES,
            default=[]
        )

    with col3:
        risk_filter = st.multiselect(
            "Risk",
            RISK_LEVELS,
            default=[]
        )

    with col4:
        sla_filter = st.multiselect(
            "SLA",
            SLA_STATUSES,
            default=[]
        )

    filtered_orders = orders.copy()

    if priority_filter and "priority" in filtered_orders.columns:
        filtered_orders = filtered_orders[
            filtered_orders["priority"]
            .astype(str)
            .str.upper()
            .isin(priority_filter)
        ]

    if status_filter and "status" in filtered_orders.columns:
        filtered_orders = filtered_orders[
            filtered_orders["status"]
            .astype(str)
            .str.upper()
            .isin(status_filter)
        ]

    if risk_filter and "risk" in filtered_orders.columns:
        filtered_orders = filtered_orders[
            filtered_orders["risk"]
            .astype(str)
            .str.upper()
            .isin(risk_filter)
        ]

    if sla_filter and "sla_status" in filtered_orders.columns:
        filtered_orders = filtered_orders[
            filtered_orders["sla_status"]
            .astype(str)
            .str.upper()
            .isin(sla_filter)
        ]

    st.write(
        f"Showing **{len(filtered_orders)}** orders."
    )

    # --------------------------------------------------------
    # ORDER TABLE
    # --------------------------------------------------------

    display_columns = [
        col for col in [
            "order_id",
            "sku",
            "quantity",
            "priority",
            "status",
            "deadline",
            "sla_status",
            "risk"
        ]
        if col in filtered_orders.columns
    ]

    if filtered_orders.empty:

        st.warning(
            "No orders match the selected filters."
        )
        return

    st.dataframe(
        filtered_orders[display_columns],
        width="stretch",
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------------
    # ORDER DETAIL
    # --------------------------------------------------------

    st.subheader("Order Detail")

    order_ids = filtered_orders["order_id"].astype(str).tolist()

    selected_order_id = st.selectbox(
        "Select an order",
        order_ids
    )

    selected_order = orders[
        orders["order_id"].astype(str) == selected_order_id
    ]

    if selected_order.empty:
        st.warning("Order not found.")
        return

    order_row = selected_order.iloc[0]

    details = get_order_details(
        selected_order_id,
        orders,
        inventory,
        exceptions,
        shipments
    )

    # --------------------------------------------------------
    # ORDER SUMMARY
    # --------------------------------------------------------

    st.markdown("### Order Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Priority",
            str(order_row.get("priority", "N/A"))
        )

    with col2:
        st.metric(
            "Status",
            str(order_row.get("status", "N/A"))
        )

    with col3:
        st.metric(
            "SLA",
            str(order_row.get("sla_status", "N/A"))
        )

    with col4:
        st.metric(
            "Risk",
            str(order_row.get("risk", "N/A"))
        )

    # --------------------------------------------------------
    # PRODUCT & INVENTORY
    # --------------------------------------------------------

    st.markdown("### Product & Inventory")

    if details:

        detail_col1, detail_col2, detail_col3, detail_col4 = (
            st.columns(4)
        )

        with detail_col1:
            st.metric(
                "SKU",
                str(details.get("sku", "N/A"))
            )

        with detail_col2:
            st.metric(
                "Required",
                format_number(details.get("required_qty", 0))
            )

        with detail_col3:
            st.metric(
                "Main Available",
                format_number(
                    details.get("main_available", 0)
                )
            )

        with detail_col4:
            st.metric(
                "Overflow Available",
                format_number(
                    details.get("overflow_available", 0)
                )
            )

        shortage = details.get("shortage", 0)
        transfer_qty = details.get("transfer_qty", 0)

        if shortage > 0:

            if transfer_qty > 0:
                st.warning(
                    f"Main warehouse is short by "
                    f"{format_number(shortage)} unit(s). "
                    f"Transfer {format_number(transfer_qty)} "
                    f"unit(s) from overflow."
                )
            else:
                st.error(
                    "Inventory is insufficient across "
                    "the available warehouses."
                )

        else:
            st.success(
                "Required inventory is available."
            )

    # --------------------------------------------------------
    # RECOMMENDED ACTION
    # --------------------------------------------------------

    st.markdown("### Recommended Action")

    recommended_action = get_recommended_action(
        details
    )

    st.info(recommended_action)

    # --------------------------------------------------------
    # EXCEPTIONS
    # --------------------------------------------------------

    st.markdown("### Order Exceptions")

    order_exceptions = exceptions[
        exceptions["order_id"].astype(str)
        == selected_order_id
    ].copy()

    if not order_exceptions.empty:

        if "recommended_action" not in order_exceptions.columns:
            order_exceptions["recommended_action"] = (
                order_exceptions.apply(
                    get_exception_action,
                    axis=1
                )
            )

        display_columns = [
            col for col in [
                "exception_id",
                "type",
                "severity",
                "status",
                "recommended_action"
            ]
            if col in order_exceptions.columns
        ]

        st.dataframe(
            order_exceptions[
                display_columns
            ],
            width="stretch",
            hide_index=True
        )

    else:
        st.success(
            "No exceptions recorded for this order."
        )

    # --------------------------------------------------------
    # SHIPMENT
    # --------------------------------------------------------

    st.markdown("### Shipment")

    order_shipments = shipments[
        shipments["order_id"].astype(str)
        == selected_order_id
    ].copy()

    if not order_shipments.empty:

        shipment_row = order_shipments.iloc[0]

        shipment_data = {}

        for column in [
            "shipment_id",
            "status",
            "scheduled_pickup",
            "pickup_risk"
        ]:
            if column in shipment_row.index:
                shipment_data[column] = shipment_row[column]

        if "pickup_risk" in shipment_row.index:
            shipment_data["recommended_action"] = (
                get_pickup_action(shipment_row)
            )

        st.dataframe(
            pd.DataFrame([shipment_data]),
            width="stretch",
            hide_index=True
        )

    else:
        st.info(
            "No shipment record found for this order."
        )


# ============================================================
# INVENTORY PAGE
# ============================================================

def show_inventory():

    st.header("Inventory Control")

    st.caption(
        "Compare main warehouse and overflow stock and "
        "identify transfer opportunities."
    )

    # --------------------------------------------------------
    # MAIN WAREHOUSE INVENTORY
    # --------------------------------------------------------

    st.subheader("Main Warehouse Inventory")

    main_inventory = inventory[
        inventory["warehouse"]
        .astype(str)
        .str.upper() == "MAIN"
    ].copy()

    if main_inventory.empty:
        st.warning(
            "No main warehouse inventory found."
        )
    else:

        display_columns = [
            col for col in [
                "sku",
                "available_qty",
                "reserved_qty",
                "net_available"
            ]
            if col in main_inventory.columns
        ]

        st.dataframe(
            main_inventory[display_columns],
            width="stretch",
            hide_index=True
        )

    # --------------------------------------------------------
    # NEGATIVE INVENTORY
    # --------------------------------------------------------

    negative_inventory = main_inventory[
        main_inventory["net_available"] < 0
    ].copy()

    if not negative_inventory.empty:

        st.warning(
            f"{len(negative_inventory)} SKU(s) have negative "
            "net availability and need attention."
        )

    # --------------------------------------------------------
    # TRANSFER CHECK
    # --------------------------------------------------------

    st.divider()

    st.subheader("Transfer Check")

    sku_options = inventory["sku"].dropna().astype(str).unique().tolist()

    if not sku_options:
        st.info("No inventory records available.")
        return

    selected_sku = st.selectbox(
        "Select SKU",
        sku_options
    )

    qty_required = st.number_input(
        "Required Quantity",
        min_value=1,
        value=1,
        step=1
    )

    transfer_result = get_transfer_recommendation(
        selected_sku,
        qty_required,
        inventory
    )

    if isinstance(transfer_result, dict):

        main_available = transfer_result.get(
            "main_available",
            transfer_result.get(
                "main_net_available",
                0
            )
        )

        overflow_available = transfer_result.get(
            "overflow_available",
            transfer_result.get(
                "overflow_net_available",
                0
            )
        )

        transfer_qty = transfer_result.get(
            "transferable",
            0
        )

        shortage = transfer_result.get(
            "shortage",
            max(qty_required - main_available, 0)
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Required",
                format_number(qty_required)
            )

        with col2:
            st.metric(
                "Main Available",
                format_number(main_available)
            )

        with col3:
            st.metric(
                "Overflow Available",
                format_number(overflow_available)
            )

        with col4:
            st.metric(
                "Transfer Qty",
                format_number(transfer_qty)
            )

        if transfer_qty > 0:

            st.success(
                f"Transfer {format_number(transfer_qty)} "
                f"unit(s) from overflow to main warehouse."
            )

        elif shortage > 0:

            st.error(
                "Inventory is insufficient across both "
                "warehouses."
            )

        else:

            st.info(
                "No transfer is required."
            )

    else:

        st.info(
            str(transfer_result)
        )


# ============================================================
# EXCEPTIONS PAGE
# ============================================================

def show_exceptions():

    st.header("Exception Management")

    st.caption(
        "Track operational issues and determine the next "
        "action required."
    )

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    open_df = get_open_exceptions(exceptions)

    if open_df is None:
        open_df = pd.DataFrame()

    open_count = len(open_df)

    if open_count > 0:

        severity_series = (
            open_df["severity"]
            .astype(str)
            .str.upper()
        )

        critical_count = int(
            (severity_series == "CRITICAL").sum()
        )

        high_count = int(
            (severity_series == "HIGH").sum()
        )

    else:
        critical_count = 0
        high_count = 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Open Exceptions",
            format_number(open_count)
        )

    with col2:
        st.metric(
            "Critical",
            format_number(critical_count)
        )

    with col3:
        st.metric(
            "High",
            format_number(high_count)
        )

    st.divider()

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    severity_filter = st.multiselect(
        "Filter by Severity",
        ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default=[]
    )

    filtered_exceptions = open_df.copy()

    if (
        severity_filter
        and not filtered_exceptions.empty
        and "severity" in filtered_exceptions.columns
    ):

        filtered_exceptions = filtered_exceptions[
            filtered_exceptions["severity"]
            .astype(str)
            .str.upper()
            .isin(severity_filter)
        ]

    # --------------------------------------------------------
    # EXCEPTION TABLE
    # --------------------------------------------------------

    if filtered_exceptions.empty:

        st.success(
            "No exceptions match the selected filter."
        )
        return

    if "recommended_action" not in filtered_exceptions.columns:

        filtered_exceptions = filtered_exceptions.copy()

        filtered_exceptions["recommended_action"] = (
            filtered_exceptions.apply(
                get_exception_action,
                axis=1
            )
        )

    display_columns = [
        col for col in [
            "exception_id",
            "order_id",
            "type",
            "severity",
            "status",
            "created_at",
            "recommended_action"
        ]
        if col in filtered_exceptions.columns
    ]

    st.dataframe(
        filtered_exceptions[
            display_columns
        ],
        width="stretch",
        hide_index=True
    )


# ============================================================
# SHIPMENTS PAGE
# ============================================================

def show_shipments():

    st.header("🚚 Shipment Control")

    st.caption(
        "Monitor shipment readiness, staging locations, "
        "and courier pickup risks."
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    metrics = get_shipment_metrics(shipments)

    scheduled_count = metrics.get(
        "scheduled",
        0
    )

    ready_count = metrics.get(
        "ready",
        0
    )

    picked_up_count = metrics.get(
        "picked_up",
        0
    )

    overdue_count = metrics.get(
        "pickup_overdue",
        0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Scheduled",
            format_number(scheduled_count)
        )

    with col2:
        st.metric(
            "Ready",
            format_number(ready_count)
        )

    with col3:
        st.metric(
            "Picked Up",
            format_number(picked_up_count)
        )

    with col4:
        st.metric(
            "Pickup Overdue",
            format_number(overdue_count)
        )

    st.divider()

    # --------------------------------------------------------
    # OVERDUE PICKUPS
    # --------------------------------------------------------

    st.subheader("🚨 Overdue Pickups")

    overdue_pickups = get_overdue_pickups(
        shipments
    )

    if (
        overdue_pickups is not None
        and not overdue_pickups.empty
    ):

        overdue_display = overdue_pickups.copy()

        overdue_display["recommended_action"] = (
            overdue_display.apply(
                get_pickup_action,
                axis=1
            )
        )

        display_columns = [
            col
            for col in [
                "order_id",
                "courier",
                "pickup_time",
                "staging_location",
                "tracking_id",
                "pickup_status",
                "pickup_risk",
                "recommended_action"
            ]
            if col in overdue_display.columns
        ]

        st.dataframe(
            overdue_display[
                display_columns
            ],
            width="stretch",
            hide_index=True
        )

    else:

        st.success(
            "No overdue courier pickups."
        )

    # --------------------------------------------------------
    # DUE SOON PICKUPS
    # --------------------------------------------------------

    due_soon_pickups = get_due_soon_pickups(
        shipments
    )

    if (
        due_soon_pickups is not None
        and not due_soon_pickups.empty
    ):

        st.warning(
            f"{len(due_soon_pickups)} shipment(s) "
            "have pickup scheduled within the next hour."
        )

        due_soon_display = due_soon_pickups.copy()

        due_soon_display["recommended_action"] = (
            due_soon_display.apply(
                get_pickup_action,
                axis=1
            )
        )

        display_columns = [
            col
            for col in [
                "order_id",
                "courier",
                "pickup_time",
                "staging_location",
                "tracking_id",
                "pickup_status",
                "pickup_risk",
                "recommended_action"
            ]
            if col in due_soon_display.columns
        ]

        st.dataframe(
            due_soon_display[
                display_columns
            ],
            width="stretch",
            hide_index=True
        )

    # --------------------------------------------------------
    # SHIPMENT QUEUE
    # --------------------------------------------------------

    st.divider()

    st.subheader("📦 Shipment Queue")

    shipment_queue = shipments.copy()

    shipment_queue["recommended_action"] = (
        shipment_queue.apply(
            get_pickup_action,
            axis=1
        )
    )

    display_columns = [
        col
        for col in [
            "order_id",
            "courier",
            "pickup_time",
            "staging_location",
            "tracking_id",
            "pickup_status",
            "pickup_risk",
            "recommended_action"
        ]
        if col in shipment_queue.columns
    ]

    st.dataframe(
        shipment_queue[
            display_columns
        ],
        width="stretch",
        hide_index=True
    )


# ============================================================
# PAGE ROUTING
# ============================================================

if page == "Dashboard":
    show_dashboard()

elif page == "Orders":
    show_orders()

elif page == "Inventory":
    show_inventory()

elif page == "Exceptions":
    show_exceptions()

elif page == "Shipments":
    show_shipments()