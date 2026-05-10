from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID
from datetime import datetime
from database import get_pg_db, get_mongo_db
from models.customer import Customer
from schemas.customer import (
    CustomerCreate, CustomerUpdate,
    CustomerResponse, CustomerListResponse
)
from config.auth_utils import get_current_user, require_manager, require_admin
from models.user import User
import math

router = APIRouter()

@router.post("/", response_model=CustomerResponse)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_manager)
):
    # Check if email already exists
    existing = db.query(Customer).filter(Customer.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists"
        )

    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)

    # Log to MongoDB
    mongo = get_mongo_db()
    mongo.activity_logs.insert_one({
        "event": "customer_created",
        "customer_id": str(customer.id),
        "customer_email": customer.email,
        "created_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    return customer

@router.get("/", response_model=CustomerListResponse)
def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Customer)

    # Search by name or email
    if search:
        query = query.filter(
            or_(
                Customer.first_name.ilike(f"%{search}%"),
                Customer.last_name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
                Customer.phone.ilike(f"%{search}%")
            )
        )

    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)

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

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_manager)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)

    # Log to MongoDB
    mongo = get_mongo_db()
    mongo.activity_logs.insert_one({
        "event": "customer_updated",
        "customer_id": str(customer.id),
        "updated_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    return customer

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(require_admin)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Soft delete
    customer.is_active = False
    db.commit()

    # Log to MongoDB
    mongo = get_mongo_db()
    mongo.activity_logs.insert_one({
        "event": "customer_deleted",
        "customer_id": str(customer_id),
        "deleted_by": current_user.email,
        "timestamp": datetime.utcnow()
    })

    return {"message": "Customer deactivated successfully"}