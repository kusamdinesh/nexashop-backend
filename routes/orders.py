from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID
from datetime import datetime
import math
import random
import string

from database import get_pg_db, get_mongo_db
from models.order import Order, OrderItem
from models.product import Product
from models.customer import Customer
from models.user import User
from schemas.order import (
    OrderCreate, OrderResponse, OrderListResponse,
    OrderStatusUpdate, OrderItemResponse
)
from config.auth_utils import get_current_user

router = APIRouter()

# ── Valid order statuses ─────────────────────────────
VALID_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]

def generate_order_number() -> str:
    """Generate unique order number like ORD-A3F2B1"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD-{suffix}"

def get_order_with_items(order: Order, db: Session) -> dict:
    """Build order response with items"""
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "status": order.status,
        "subtotal": order.subtotal,
        "tax": order.tax,
        "total": order.total,
        "notes": order.notes,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price
            }
            for item in items
        ]
    }

@router.post("/", response_model=OrderResponse)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if not data.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    # Calculate totals
    subtotal = 0.0
    order_items = []

    for item_data in data.items:
        product = db.query(Product).filter(
            Product.id == item_data.product_id,
            Product.is_active == True
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item_data.product_id} not found"
            )

        if product.stock_quantity < item_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
            )

        item_total = product.price * item_data.quantity
        subtotal += item_total

        order_items.append({
            "product": product,
            "quantity": item_data.quantity,
            "unit_price": product.price,
            "total_price": item_total
        })

    # Calculate tax and total
    tax = round(subtotal * 0.1, 2)
    total = round(subtotal + tax, 2)
    subtotal = round(subtotal, 2)

    # Create order
    order = Order(
        order_number=generate_order_number(),
        customer_id=data.customer_id,
        status="pending",
        subtotal=subtotal,
        tax=tax,
        total=total,
        notes=data.notes
    )
    db.add(order)
    db.flush()

    # Create order items and update stock
    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product"].id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            total_price=item_data["total_price"]
        )
        db.add(order_item)

        # Deduct stock
        item_data["product"].stock_quantity -= item_data["quantity"]

    # Update customer stats
    customer.total_orders += 1
    customer.total_spent += total

    db.commit()
    db.refresh(order)

    # Log to MongoDB
    mongo = get_mongo_db()
    mongo.activity_logs.insert_one({
        "event": "order_created",
        "order_id": str(order.id),
        "order_number": order.order_number,
        "customer_id": str(data.customer_id),
        "total": total,
        "created_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    return get_order_with_items(order, db)

@router.get("/", response_model=OrderListResponse)
def get_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    if search:
        query = query.filter(Order.order_number.ilike(f"%{search}%"))

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    orders = query.order_by(Order.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [get_order_with_items(o, db) for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return get_order_with_items(order, db)

@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: UUID,
    data: OrderStatusUpdate,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    if data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
        )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    old_status = order.status
    order.status = data.status
    db.commit()
    db.refresh(order)

    # If cancelled — restore stock
    if data.status == "cancelled" and old_status != "cancelled":
        items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock_quantity += item.quantity

        # Update customer stats
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if customer:
            customer.total_orders = max(0, customer.total_orders - 1)
            customer.total_spent = max(0, customer.total_spent - order.total)

        db.commit()

    # Log to MongoDB
    mongo = get_mongo_db()
    mongo.activity_logs.insert_one({
        "event": "order_status_updated",
        "order_id": str(order.id),
        "order_number": order.order_number,
        "old_status": old_status,
        "new_status": data.status,
        "updated_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    return get_order_with_items(order, db)

@router.delete("/{order_id}")
def cancel_order(
    order_id: UUID,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "delivered":
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a delivered order"
        )

    order.status = "cancelled"

    # Restore stock
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock_quantity += item.quantity

    # Update customer stats
    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    if customer:
        customer.total_orders = max(0, customer.total_orders - 1)
        customer.total_spent = max(0, customer.total_spent - order.total)

    db.commit()

    # Log to MongoDB
    mongo = get_mongo_db()
    mongo.activity_logs.insert_one({
        "event": "order_cancelled",
        "order_id": str(order_id),
        "cancelled_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    return {"message": "Order cancelled successfully"}