from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID
from datetime import datetime
import math

from database import get_pg_db, get_mongo_db
from models.product import Product, Category
from models.user import User
from config.auth_utils import get_current_user, require_manager
from pydantic import BaseModel
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache
from config.email_service import send_low_stock_alert

router = APIRouter()

class StockAdjustment(BaseModel):
    product_id: UUID
    adjustment: int
    reason: str

@router.get("/")
@cache(expire=120)
def get_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product).filter(Product.is_active == True)

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )

    if status == "out":
        query = query.filter(Product.stock_quantity == 0)
    elif status == "low":
        query = query.filter(
            Product.stock_quantity > 0,
            Product.stock_quantity < 10
        )
    elif status == "ok":
        query = query.filter(Product.stock_quantity >= 10)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    products = query.order_by(
        Product.stock_quantity.asc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    # Get category names
    categories = {str(c.id): c.name for c in db.query(Category).all()}

    items = [
        {
            "id": str(p.id),
            "name": p.name,
            "sku": p.sku,
            "price": p.price,
            "stock_quantity": p.stock_quantity,
            "category": categories.get(str(p.category_id), "Uncategorized"),
            "status": "out" if p.stock_quantity == 0
                      else "low" if p.stock_quantity < 10
                      else "ok"
        }
        for p in products
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "summary": {
            "total": db.query(Product).filter(Product.is_active == True).count(),
            "out_of_stock": db.query(Product).filter(
                Product.stock_quantity == 0,
                Product.is_active == True
            ).count(),
            "low_stock": db.query(Product).filter(
                Product.stock_quantity > 0,
                Product.stock_quantity < 10,
                Product.is_active == True
            ).count(),
            "well_stocked": db.query(Product).filter(
                Product.stock_quantity >= 10,
                Product.is_active == True
            ).count()
        }
    }

@router.post("/adjust")
async def adjust_stock(
    data: StockAdjustment,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_manager)
):
    product = db.query(Product).filter(
        Product.id == data.product_id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_quantity = product.stock_quantity + data.adjustment

    if new_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce stock below 0. Current stock: {product.stock_quantity}"
        )

    old_quantity = product.stock_quantity
    product.stock_quantity = new_quantity
    # Check for low stock and alert admin
    low_stock_products = db.query(Product).filter(
        Product.is_active == True,
        Product.stock_quantity < 10
    ).all()

    if low_stock_products:
        alert_products = [
            {
                "name": p.name,
                "sku": p.sku,
                "stock": p.stock_quantity,
                "status": "out" if p.stock_quantity == 0 else "low"
            }
            for p in low_stock_products
        ]
        send_low_stock_alert(alert_products)
    db.commit()

    # Log to MongoDB
    mongo = get_mongo_db()
    mongo.stock_history.insert_one({
        "product_id": str(product.id),
        "product_name": product.name,
        "sku": product.sku,
        "old_quantity": old_quantity,
        "adjustment": data.adjustment,
        "new_quantity": new_quantity,
        "reason": data.reason,
        "adjusted_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    mongo.activity_logs.insert_one({
        "event": "stock_adjusted",
        "product_name": product.name,
        "adjustment": data.adjustment,
        "adjusted_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    await FastAPICache.clear(namespace="nexashop-cache")
    return {
        "message": "Stock adjusted successfully",
        "product": product.name,
        "old_quantity": old_quantity,
        "adjustment": data.adjustment,
        "new_quantity": new_quantity
    }

@router.get("/history")
def get_stock_history(
    product_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    mongo = get_mongo_db()
    query = {}
    if product_id:
        query["product_id"] = product_id

    history = list(
        mongo.stock_history
        .find(query, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )

    for item in history:
        if "timestamp" in item:
            item["timestamp"] = item["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

    return history