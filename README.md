# Fulfilment Hub

An operations control center for managing e-commerce order fulfilment, SLA risks, inventory availability, exceptions, and courier pickups.

## Problem Statement

E-commerce fulfilment teams need to continuously track orders across different stages while making sure priority orders meet their SLA.

In the current process, order visibility, inventory availability, exceptions, and courier pickup status can become difficult to track when information is maintained across spreadsheets and informal communication.

Fulfilment Hub provides a single operational view to help warehouse and office teams quickly identify:

- Which orders need attention
- Which priority orders are at risk
- Whether required inventory is available
- Whether inventory should be transferred from overflow stores
- Which operational exceptions are still open
- Which courier pickups are overdue or due soon

## Key Features

### 1. Operations Dashboard

Provides a high-level view of fulfilment operations through:

- Total orders
- Priority orders
- At-risk orders
- Open exceptions
- Ready-to-ship orders
- Order pipeline
- Urgent orders

### 2. Action Center

Highlights the operational issues that should be handled first:

- Critical orders
- Inventory transfer opportunities
- Open exceptions
- Recommended next actions

### 3. Order Detail

Allows the operator to inspect an individual order and view:

- Order status
- Priority
- SLA status
- Risk level
- SKU and quantity
- Main warehouse availability
- Overflow availability
- Exceptions
- Recommended action

### 4. Inventory Control

Provides visibility into inventory across:

- Main warehouse
- Overflow locations

The application calculates:

`Net Available = Available Quantity - Reserved Quantity`

It also identifies negative availability and recommends inventory transfers when the main warehouse does not have sufficient stock but overflow inventory is available.

### 5. Exception Management

Tracks operational issues such as:

- Inventory shortage
- Inventory mismatch
- Wrong variant
- Wrong product
- Misplaced box
- Courier delay

Exceptions are categorized by severity and status so operators can prioritize the most important issues.

### 6. Shipment Control

Tracks courier pickup operations including:

- Scheduled pickups
- Ready packages
- Picked-up shipments
- Overdue pickups
- Pickups due soon

The application also provides a recommended next action for shipment-related risks.

## Fulfilment Workflow

The application models the fulfilment process as:

`RECEIVED → PROCESSING → PICKING → PACKING → STAGED → SHIPPED`

Operational exceptions are separately identified so that issues do not remain hidden within the normal workflow.

## SLA and Risk Logic

Orders are evaluated based on their SLA deadline.

### SLA Status

- **ON TRACK** — deadline is more than 60 minutes away
- **DUE SOON** — deadline is within 60 minutes
- **OVERDUE** — deadline has already passed

### Risk Levels

The application combines order priority and SLA status to determine operational risk.

Examples:

- High-priority + overdue → **CRITICAL**
- Overdue → **HIGH**
- High-priority + due soon → **HIGH**
- Due soon → **MEDIUM**
- Otherwise → **LOW**

This helps the operations team focus on orders that require immediate intervention.

## Inventory Transfer Logic

When an order requires inventory, the application checks main warehouse availability.

If the main warehouse does not have enough net inventory but an overflow location has sufficient stock, the application recommends a transfer.

Example:

```text
Required Quantity : 3
Main Net Available: -2
Overflow Available: 25
Recommended Action: Transfer inventory from overflow to main warehouse
