from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routes import auth, products, orders, customers, inventory, analytics, users

# Create all PostgreSQL tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NexaShop API",
    description="E-Commerce Platform API",
    version="1.0.0",
    swagger_ui_oauth2_redirect_url="/api/v1/auth/login",
)

# Allow Angular frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API version prefix
V1 = "/api/v1"

# Register all route modules with versioned URL prefixes
app.include_router(auth.router,      prefix=f"{V1}/auth",      tags=["Auth"])
app.include_router(products.router,  prefix=f"{V1}/products",  tags=["Products"])
app.include_router(orders.router,    prefix=f"{V1}/orders",    tags=["Orders"])
app.include_router(customers.router, prefix=f"{V1}/customers", tags=["Customers"])
app.include_router(inventory.router, prefix=f"{V1}/inventory", tags=["Inventory"])
app.include_router(analytics.router, prefix=f"{V1}/analytics", tags=["Analytics"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

@app.get("/")
def root():
    return {
        "message": "Welcome to NexaShop API",
        "version": "v1",
        "docs": "/docs"
    }