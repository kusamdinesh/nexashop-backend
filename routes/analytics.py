from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from database import get_pg_db, get_mongo_db
from config.auth_utils import get_current_user
from models.user import User
from models.customer import Customer
from models.product import Product

router = APIRouter()

@router.get("/summary")
def get_summary(
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    # ── PostgreSQL Stats ────────────────────────────
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_customers = db.query(Customer).filter(Customer.is_active == True).count()
    low_stock_products = db.query(Product).filter(
        Product.stock_quantity < 10,
        Product.is_active == True
    ).count()
    total_revenue = db.query(
        func.sum(Customer.total_spent)
    ).scalar() or 0.0
    total_orders = db.query(
        func.sum(Customer.total_orders)
    ).scalar() or 0

    return {
        "total_products": total_products,
        "total_customers": total_customers,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "low_stock_products": low_stock_products
    }

@router.get("/top-products")
def get_top_products(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    # Get products with lowest stock first as a proxy for most sold
    products = db.query(Product).filter(
        Product.is_active == True
    ).order_by(Product.stock_quantity.asc()).limit(limit).all()

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "sku": p.sku,
            "price": p.price,
            "stock_quantity": p.stock_quantity
        }
        for p in products
    ]

@router.get("/customer-growth")
def get_customer_growth(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user)
):
    # Get customer registration events from MongoDB
    mongo = get_mongo_db()
    since = datetime.utcnow() - timedelta(days=days)

    pipeline = [
        {
            "$match": {
                "event": "user_registered",
                "timestamp": {"$gte": since}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp"
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]

    results = list(mongo.activity_logs.aggregate(pipeline))
    return [{"date": r["_id"], "count": r["count"]} for r in results]

@router.get("/recent-activity")
def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    # Get recent activity logs from MongoDB
    mongo = get_mongo_db()
    logs = list(
        mongo.activity_logs
        .find({}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )

    # Convert datetime to string for JSON serialization
    for log in logs:
        if "timestamp" in log:
            log["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

    return logs

@router.get("/activity-breakdown")
def get_activity_breakdown(
    current_user: User = Depends(get_current_user)
):
    # Count events by type from MongoDB
    mongo = get_mongo_db()
    pipeline = [
        {
            "$group": {
                "_id": "$event",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]

    results = list(mongo.activity_logs.aggregate(pipeline))
    return [{"event": r["_id"], "count": r["count"]} for r in results]