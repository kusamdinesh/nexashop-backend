from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID
from datetime import datetime
from database import get_pg_db, get_mongo_db
from models.product import Product, Category
from schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductListResponse, CategoryCreate, CategoryResponse
)
from config.auth_utils import get_current_user, require_manager, require_admin
from models.user import User
import math

router = APIRouter()

# ── Category Routes ─────────────────────────────────

@router.post("/categories", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_manager)
):
    # Check if category already exists
    existing = db.query(Category).filter(Category.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category already exists"
        )
    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Category).all()

# ── Product Routes ──────────────────────────────────

@router.post("/", response_model=ProductResponse)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_manager)
):
    # Check SKU is unique
    existing = db.query(Product).filter(Product.sku == data.sku).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SKU already exists"
        )

    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)

    # Log to MongoDB
    mongo = get_mongo_db()
    mongo.activity_logs.insert_one({
        "event": "product_created",
        "product_id": str(product.id),
        "product_name": product.name,
        "created_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    return product

@router.get("/", response_model=ProductListResponse)
def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product)

    # Apply filters
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    # Pagination
    total = query.count()
    total_pages = math.ceil(total / page_size)
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_manager)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Update only fields that were sent
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    # Log to MongoDB
    mongo = get_mongo_db()
    mongo.activity_logs.insert_one({
        "event": "product_updated",
        "product_id": str(product.id),
        "updated_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    return product

@router.delete("/{product_id}")
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Soft delete — just deactivate
    product.is_active = False
    db.commit()

    # Log to MongoDB
    mongo = get_mongo_db()
    mongo.activity_logs.insert_one({
        "event": "product_deleted",
        "product_id": str(product_id),
        "deleted_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    return {"message": "Product deactivated successfully"}