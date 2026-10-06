import os
import random
from datetime import datetime, timedelta

import pandas as pd


# =========================================================
# CONFIGURATION
# =========================================================

random.seed(42)

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)


# =========================================================
# PRODUCT MASTER
# =========================================================

products = [
    ["SKU001", "Ceramic Bowl", "White", "Kitchen"],
    ["SKU002", "Dinner Plate", "White", "Kitchen"],
    ["SKU003", "Serving Tray", "Large", "Kitchen"],
    ["SKU004", "Coffee Mug", "Blue", "Kitchen"],
    ["SKU005", "Water Bottle", "Black", "Drinkware"],
    ["SKU006", "Ceramic Bowl", "Blue", "Kitchen"],
    ["SKU007", "Dinner Plate", "Blue", "Kitchen"],
    ["SKU008", "Storage Box", "Medium", "Storage"],
    ["SKU009", "Cutlery Set", "Standard", "Kitchen"],
    ["SKU010", "Glass Tumbler", "Clear", "Drinkware"],
]

products_df = pd.DataFrame(
    products,
    columns=[
        "sku",
        "product_name",
        "variant",
        "category",
    ],
)

products_df.to_csv(
    f"{DATA_DIR}/products.csv",
    index=False
)


# =========================================================
# INVENTORY
# =========================================================

inventory_data = [
    # MAIN warehouse
    ["SKU001", "MAIN", 32, 8],
    ["SKU002", "MAIN", 18, 12],
    ["SKU003", "MAIN", 7, 5],
    ["SKU004", "MAIN", 25, 10],
    ["SKU005", "MAIN", 40, 15],
    ["SKU006", "MAIN", 12, 4],

    # Deliberate shortage
    ["SKU007", "MAIN", 5, 7],

    ["SKU008", "MAIN", 20, 8],
    ["SKU009", "MAIN", 15, 6],
    ["SKU010", "MAIN", 30, 12],

    # OVERFLOW warehouse
    ["SKU001", "OVERFLOW", 25, 0],
    ["SKU002", "OVERFLOW", 30, 0],
    ["SKU003", "OVERFLOW", 15, 0],
    ["SKU004", "OVERFLOW", 20, 0],
    ["SKU005", "OVERFLOW", 15, 0],
    ["SKU006", "OVERFLOW", 10, 0],
    ["SKU007", "OVERFLOW", 25, 0],
    ["SKU008", "OVERFLOW", 20, 0],
    ["SKU009", "OVERFLOW", 10, 0],
    ["SKU010", "OVERFLOW", 15, 0],
]

inventory_df = pd.DataFrame(
    inventory_data,
    columns=[
        "sku",
        "warehouse",
        "available_qty",
        "reserved_qty",
    ],
)

inventory_df.to_csv(
    f"{DATA_DIR}/inventory.csv",
    index=False
)


# =========================================================
# ORDER GENERATION
# =========================================================

customers = [
    "Customer 001",
    "Customer 002",
    "Customer 003",
    "Customer 004",
    "Customer 005",
    "Customer 006",
    "Customer 007",
    "Customer 008",
    "Customer 009",
    "Customer 010",
    "Customer 011",
    "Customer 012",
    "Customer 013",
    "Customer 014",
    "Customer 015",
    "Customer 016",
    "Customer 017",
    "Customer 018",
    "Customer 019",
    "Customer 020",
]

couriers = [
    "Courier A",
    "Courier B",
    "Courier C",
]

statuses = [
    "RECEIVED",
    "PROCESSING",
    "PICKING",
    "PACKING",
    "STAGED",
]

skus = [
    product[0]
    for product in products
]


# Use today's date so the dashboard
# demonstrates SLA behaviour immediately.
today = datetime.now().replace(
    hour=0,
    minute=0,
    second=0,
    microsecond=0
)


current_time = datetime.now()

orders = []

for i in range(1, 201):

    order_id = f"ORD{1000 + i}"

    customer = random.choice(customers)

    sku = random.choice(skus)

    quantity = random.randint(1, 5)

    priority = random.choices(
        ["HIGH", "NORMAL"],
        weights=[25, 75],
        k=1
    )[0]

    status = random.choice(statuses)

    # Generate realistic order times and deadlines
    current_time = datetime.now()

    # Orders are created around the current operating window.
    order_time = current_time - timedelta(
        hours=random.randint(0, 6),
        minutes=random.randint(0, 59)
    )

    # Most orders should still be within SLA.
    sla_type = random.choices(
        ["ON_TRACK", "DUE_SOON", "OVERDUE"],
        weights=[70, 20, 10],
        k=1
    )[0]

    if sla_type == "ON_TRACK":

        deadline = current_time + timedelta(
            hours=random.randint(2, 8),
            minutes=random.randint(0, 59)
        )

    elif sla_type == "DUE_SOON":

        deadline = current_time + timedelta(
            minutes=random.randint(15, 60)
        )

    else:

        deadline = current_time - timedelta(
            minutes=random.randint(15, 180)
        )

    courier = random.choice(couriers)

    orders.append(
        [
            order_id,
            customer,
            order_time,
            priority,
            status,
            sku,
            quantity,
            deadline,
            courier,
        ]
    )


# =========================================================
# DELIBERATE OPERATIONAL SCENARIOS
# =========================================================

# Scenario 1:
# HIGH priority + overdue
orders[0][3] = "HIGH"
orders[0][4] = "PICKING"
orders[0][7] = datetime.now() - timedelta(
    minutes=45
)

# Scenario 2:
# HIGH priority + due soon
orders[1][3] = "HIGH"
orders[1][4] = "PROCESSING"
orders[1][7] = datetime.now() + timedelta(
    minutes=30
)

# Scenario 3:
# Inventory shortage in MAIN,
# but stock available in OVERFLOW.
orders[2][5] = "SKU007"
orders[2][6] = 3
orders[2][3] = "HIGH"
orders[2][4] = "PICKING"
orders[2][7] = datetime.now() + timedelta(
    minutes=45
)

# Scenario 4:
# Normal order ready to ship.
orders[3][3] = "NORMAL"
orders[3][4] = "STAGED"
orders[3][7] = datetime.now() + timedelta(
    hours=4
)

# Scenario 5:
# Another priority order approaching deadline.
orders[4][3] = "HIGH"
orders[4][4] = "PACKING"
orders[4][7] = datetime.now() + timedelta(
    minutes=50
)


orders_df = pd.DataFrame(
    orders,
    columns=[
        "order_id",
        "customer",
        "order_time",
        "priority",
        "status",
        "sku",
        "quantity",
        "deadline",
        "courier",
    ],
)


orders_df.to_csv(
    f"{DATA_DIR}/orders.csv",
    index=False
)


# =========================================================
# SHIPMENTS
# =========================================================
shipment_data = []

current_time = datetime.now()

for i in range(1, 201):

    order_id = f"ORD{1000 + i}"

    courier = random.choice(couriers)

    staging_location = (
        f"{random.choice(['A', 'B', 'C'])}-"
        f"{random.randint(1, 10):02d}"
    )

    tracking_id = f"TRK{1000 + i}"

    # Create a realistic shipment status distribution
    pickup_status = random.choices(
        [
            "SCHEDULED",
            "READY",
            "PICKED_UP"
        ],
        weights=[41, 34, 25],
        k=1
    )[0]

    # --------------------------------------------------------
    # Pickup time based on shipment status
    # --------------------------------------------------------

    if pickup_status == "PICKED_UP":

        # Already completed shipments
        pickup_time = current_time - timedelta(
            hours=random.randint(1, 8),
            minutes=random.randint(0, 59)
        )

    elif pickup_status == "READY":

        # Mostly ready for pickup within the next few hours
        pickup_time = current_time + timedelta(
            minutes=random.randint(30, 180)
        )

    else:

        # Scheduled shipments are generally later today
        pickup_time = current_time + timedelta(
            hours=random.randint(2, 8),
            minutes=random.randint(0, 59)
        )

    shipment_data.append(
        [
            order_id,
            courier,
            pickup_time,
            staging_location,
            tracking_id,
            pickup_status,
        ]
    )


# ------------------------------------------------------------
# Deliberate overdue courier issue
# ORD1011
# ------------------------------------------------------------

shipment_data[10][5] = "SCHEDULED"

shipment_data[10][2] = current_time - timedelta(
    hours=1
)


# ------------------------------------------------------------
# Deliberate ready-to-pickup scenario
# ORD1012
# ------------------------------------------------------------

shipment_data[11][5] = "READY"

shipment_data[11][2] = current_time + timedelta(
    minutes=30
)


# ------------------------------------------------------------
# Deliberate due-soon pickup
# ORD1013
# ------------------------------------------------------------

shipment_data[12][5] = "SCHEDULED"

shipment_data[12][2] = current_time + timedelta(
    minutes=45
)


shipments_df = pd.DataFrame(
    shipment_data,
    columns=[
        "order_id",
        "courier",
        "pickup_time",
        "staging_location",
        "tracking_id",
        "pickup_status",
    ],
)


shipments_df.to_csv(
    f"{DATA_DIR}/shipments.csv",
    index=False
)

# =========================================================
# EXCEPTIONS
# =========================================================

exception_data = [
    [
        "EXC001",
        "ORD1003",
        "INVENTORY_SHORTAGE",
        "HIGH",
        "SKU007 shortage in main warehouse",
        "OPEN",
        "Warehouse Team",
        datetime.now() - timedelta(minutes=50),
    ],
    [
        "EXC002",
        "ORD1010",
        "WRONG_VARIANT",
        "CRITICAL",
        "Picked blue variant instead of white",
        "OPEN",
        "Picking Team",
        datetime.now() - timedelta(minutes=40),
    ],
    [
        "EXC003",
        "ORD1015",
        "COURIER_DELAY",
        "HIGH",
        "Courier pickup not completed",
        "OPEN",
        "Operations Team",
        datetime.now() - timedelta(minutes=30),
    ],
    [
        "EXC004",
        "ORD1020",
        "MISPLACED_BOX",
        "HIGH",
        "Packed box could not be located in staging",
        "OPEN",
        "Warehouse Team",
        datetime.now() - timedelta(minutes=20),
    ],
    [
        "EXC005",
        "ORD1025",
        "INVENTORY_MISMATCH",
        "MEDIUM",
        "System quantity differs from physical count",
        "OPEN",
        "Inventory Team",
        datetime.now() - timedelta(minutes=15),
    ],
    [
        "EXC006",
        "ORD1030",
        "WRONG_PRODUCT",
        "CRITICAL",
        "Picked SKU does not match order",
        "OPEN",
        "Picking Team",
        datetime.now() - timedelta(minutes=10),
    ],
    [
        "EXC007",
        "ORD1040",
        "COURIER_DELAY",
        "MEDIUM",
        "Courier arrival delayed",
        "RESOLVED",
        "Operations Team",
        datetime.now() - timedelta(hours=2),
    ],
]


exceptions_df = pd.DataFrame(
    exception_data,
    columns=[
        "exception_id",
        "order_id",
        "type",
        "severity",
        "description",
        "status",
        "owner",
        "created_at",
    ],
)


exceptions_df.to_csv(
    f"{DATA_DIR}/exceptions.csv",
    index=False
)


# =========================================================
# SUMMARY
# =========================================================

print()
print("=" * 60)
print("FULFILMENT HUB DATA GENERATED SUCCESSFULLY")
print("=" * 60)

print(
    f"Products created   : {len(products_df)}"
)

print(
    f"Inventory records  : {len(inventory_df)}"
)

print(
    f"Orders created     : {len(orders_df)}"
)

print(
    f"Shipments created  : {len(shipments_df)}"
)

print(
    f"Exceptions created : {len(exceptions_df)}"
)

print()
print("Files created inside the data/ folder:")
print("  ✓ products.csv")
print("  ✓ inventory.csv")
print("  ✓ orders.csv")
print("  ✓ shipments.csv")
print("  ✓ exceptions.csv")

print()
print("Deliberate test scenarios:")
print("  ✓ Priority overdue order")
print("  ✓ Priority order due soon")
print("  ✓ Main warehouse shortage")
print("  ✓ Overflow transfer opportunity")
print("  ✓ Ready-to-ship order")
print("  ✓ Courier delay")
print("  ✓ Wrong variant")
print("  ✓ Misplaced box")
print("  ✓ Inventory mismatch")

print("=" * 60)