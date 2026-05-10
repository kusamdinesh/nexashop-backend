import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, mongo_db
from models.user import User
from models.product import Product, Category
from models.customer import Customer
from models.order import Order, OrderItem
from passlib.context import CryptContext
import uuid
from datetime import datetime, timedelta
import random

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def seed():
    db = SessionLocal()
    print("🌱 Starting seed...")

    # ── Categories ──────────────────────────────────
    print("Creating categories...")
    categories = [
        Category(name="Electronics", description="Electronic devices and accessories"),
        Category(name="Clothing", description="Fashion and apparel"),
        Category(name="Home & Garden", description="Home improvement and garden"),
        Category(name="Sports", description="Sports and outdoor equipment"),
        Category(name="Books", description="Books and publications"),
    ]
    for c in categories:
        existing = db.query(Category).filter(Category.name == c.name).first()
        if not existing:
            db.add(c)
    db.commit()
    categories = db.query(Category).all()
    print(f"✅ {len(categories)} categories created")

    # ── Products ────────────────────────────────────
    print("Creating products...")
    products_data = [
        {"name": "iPhone 15 Pro", "sku": "APPLE-IP15P", "price": 999.99, "stock": 45, "cat": "Electronics"},
        {"name": "Samsung Galaxy S24", "sku": "SAM-GS24", "price": 899.99, "stock": 32, "cat": "Electronics"},
        {"name": "MacBook Pro 14\"", "sku": "APPLE-MBP14", "price": 1999.99, "stock": 18, "cat": "Electronics"},
        {"name": "iPad Air", "sku": "APPLE-IPA", "price": 599.99, "stock": 27, "cat": "Electronics"},
        {"name": "Sony WH-1000XM5", "sku": "SONY-WH1000", "price": 349.99, "stock": 54, "cat": "Electronics"},
        {"name": "Nike Air Max 270", "sku": "NIKE-AM270", "price": 149.99, "stock": 68, "cat": "Clothing"},
        {"name": "Adidas Ultraboost", "sku": "ADID-UB22", "price": 189.99, "stock": 43, "cat": "Clothing"},
        {"name": "Levi's 501 Jeans", "sku": "LEVI-501", "price": 79.99, "stock": 92, "cat": "Clothing"},
        {"name": "North Face Jacket", "sku": "TNF-JKT01", "price": 249.99, "stock": 31, "cat": "Clothing"},
        {"name": "Dyson V15 Vacuum", "sku": "DYSON-V15", "price": 749.99, "stock": 14, "cat": "Home & Garden"},
        {"name": "Instant Pot Duo", "sku": "INSTPOT-DUO", "price": 99.99, "stock": 56, "cat": "Home & Garden"},
        {"name": "Weber Grill", "sku": "WEBER-GRL", "price": 399.99, "stock": 9, "cat": "Home & Garden"},
        {"name": "Yoga Mat Pro", "sku": "YOGA-MAT01", "price": 69.99, "stock": 78, "cat": "Sports"},
        {"name": "Garmin Forerunner", "sku": "GARM-FR255", "price": 349.99, "stock": 23, "cat": "Sports"},
        {"name": "Peloton Bike", "sku": "PELO-BIKE1", "price": 1445.00, "stock": 6, "cat": "Sports"},
        {"name": "Atomic Habits", "sku": "BOOK-ATOMHAB", "price": 18.99, "stock": 120, "cat": "Books"},
        {"name": "The Pragmatic Programmer", "sku": "BOOK-PRAGPROG", "price": 49.99, "stock": 45, "cat": "Books"},
        {"name": "Clean Code", "sku": "BOOK-CLNCODE", "price": 44.99, "stock": 38, "cat": "Books"},
    ]

    category_map = {c.name: c.id for c in categories}
    created_products = []

    for p in products_data:
        existing = db.query(Product).filter(Product.sku == p["sku"]).first()
        if not existing:
            product = Product(
                name=p["name"],
                sku=p["sku"],
                price=p["price"],
                stock_quantity=p["stock"],
                category_id=category_map.get(p["cat"]),
                description=f"High quality {p['name']} — premium product",
                is_active=True
            )
            db.add(product)
            created_products.append(product)

    db.commit()
    all_products = db.query(Product).all()
    print(f"✅ {len(all_products)} products created")

    # ── Users with different roles ───────────────────────
    print("Creating users with roles...")

    users_data = [
        {
            "full_name": "Admin User",
            "email": "admin@nexashop.com",
            "password": "Admin123!",
            "role": "admin",
            "is_admin": True
        },
        {
            "full_name": "Sarah Manager",
            "email": "manager@nexashop.com",
            "password": "Manager123!",
            "role": "manager",
            "is_admin": False
        },
        {
            "full_name": "Tom Staff",
            "email": "staff@nexashop.com",
            "password": "Staff123!",
            "role": "staff",
            "is_admin": False
        },
    ]

    for u in users_data:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            user = User(
                full_name=u["full_name"],
                email=u["email"],
                hashed_password=pwd_context.hash(u["password"]),
                role=u["role"],
                is_admin=u["is_admin"],
                is_active=True
            )
            db.add(user)

    db.commit()
    print("✅ Users created:")
    print("   👑 admin@nexashop.com / Admin123!")
    print("   👔 manager@nexashop.com / Manager123!")
    print("   👤 staff@nexashop.com / Staff123!")

    # ── Customers ───────────────────────────────────
    print("Creating customers...")
    customers_data = [
        {"first": "James", "last": "Wilson", "email": "james.wilson@email.com", "phone": "555-0101", "city": "New York", "country": "USA"},
        {"first": "Emma", "last": "Johnson", "email": "emma.johnson@email.com", "phone": "555-0102", "city": "Los Angeles", "country": "USA"},
        {"first": "Oliver", "last": "Brown", "email": "oliver.brown@email.com", "phone": "555-0103", "city": "Chicago", "country": "USA"},
        {"first": "Sophia", "last": "Davis", "email": "sophia.davis@email.com", "phone": "555-0104", "city": "Houston", "country": "USA"},
        {"first": "Liam", "last": "Martinez", "email": "liam.martinez@email.com", "phone": "555-0105", "city": "Phoenix", "country": "USA"},
        {"first": "Ava", "last": "Garcia", "email": "ava.garcia@email.com", "phone": "555-0106", "city": "Philadelphia", "country": "USA"},
        {"first": "Noah", "last": "Miller", "email": "noah.miller@email.com", "phone": "555-0107", "city": "San Antonio", "country": "USA"},
        {"first": "Isabella", "last": "Taylor", "email": "isabella.taylor@email.com", "phone": "555-0108", "city": "San Diego", "country": "USA"},
        {"first": "William", "last": "Anderson", "email": "william.anderson@email.com", "phone": "555-0109", "city": "Dallas", "country": "USA"},
        {"first": "Mia", "last": "Thomas", "email": "mia.thomas@email.com", "phone": "555-0110", "city": "San Jose", "country": "USA"},
        {"first": "Benjamin", "last": "Jackson", "email": "benjamin.jackson@email.com", "phone": "555-0111", "city": "Austin", "country": "USA"},
        {"first": "Charlotte", "last": "White", "email": "charlotte.white@email.com", "phone": "555-0112", "city": "Seattle", "country": "USA"},
    ]

    created_customers = []
    for c in customers_data:
        existing = db.query(Customer).filter(Customer.email == c["email"]).first()
        if not existing:
            customer = Customer(
                first_name=c["first"],
                last_name=c["last"],
                email=c["email"],
                phone=c["phone"],
                city=c["city"],
                country=c["country"],
                is_active=True
            )
            db.add(customer)
            created_customers.append(customer)

    db.commit()
    all_customers = db.query(Customer).all()
    print(f"✅ {len(all_customers)} customers created")

    # ── Orders ──────────────────────────────────────
    print("Creating orders...")
    all_products = db.query(Product).all()
    statuses = ["pending", "processing", "shipped", "delivered", "delivered", "delivered"]

    orders_created = 0
    for i in range(20):
        customer = random.choice(all_customers)
        status = random.choice(statuses)
        num_items = random.randint(1, 3)
        selected_products = random.sample(all_products, min(num_items, len(all_products)))

        subtotal = 0.0
        order_items_data = []

        for product in selected_products:
            quantity = random.randint(1, 3)
            item_total = product.price * quantity
            subtotal += item_total
            order_items_data.append({
                "product": product,
                "quantity": quantity,
                "unit_price": product.price,
                "total_price": item_total
            })

        tax = round(subtotal * 0.1, 2)
        total = round(subtotal + tax, 2)
        subtotal = round(subtotal, 2)

        # Generate unique order number
        suffix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
        order_number = f"ORD-{suffix}"

        order = Order(
            order_number=order_number,
            customer_id=customer.id,
            status=status,
            subtotal=subtotal,
            tax=tax,
            total=total,
            notes=random.choice([None, "Please handle with care", "Gift wrap requested", "Leave at door"]),
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 60))
        )
        db.add(order)
        db.flush()

        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product"].id,
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                total_price=item_data["total_price"]
            )
            db.add(order_item)

        # Update customer stats
        customer.total_orders += 1
        customer.total_spent += total
        orders_created += 1

    db.commit()
    print(f"✅ {orders_created} orders created")

    # ── MongoDB Activity Logs ────────────────────────
    print("Creating MongoDB activity logs...")
    events = [
        "user_registered", "user_login", "product_created",
        "product_updated", "customer_created", "order_created",
        "order_status_updated"
    ]

    emails = [c["email"] for c in customers_data] + ["admin@nexashop.com"]

    for i in range(50):
        event = random.choice(events)
        mongo_db.activity_logs.insert_one({
            "event": event,
            "email": random.choice(emails),
            "timestamp": datetime.utcnow() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23)
            )
        })

    print("✅ 50 activity logs created in MongoDB")

    db.close()
    print("\n🎉 Seed complete!")
    print("👤 Admin login: admin@nexashop.com / Admin123!")

if __name__ == "__main__":
    seed()