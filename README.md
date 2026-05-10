# NexaShop Backend

A modern e-commerce REST API built with FastAPI and Python.

## Tech Stack
- FastAPI
- PostgreSQL (via SQLAlchemy)
- MongoDB (via PyMongo)
- JWT Authentication
- Argon2id Password Hashing
- Pydantic v2

## Features
- Versioned API (/api/v1)
- Auth Module (Register, Login, JWT)
- Products Module (CRUD, Categories, Search, Pagination)
- Customers Module (CRUD, Search)
- Analytics Module (PostgreSQL + MongoDB)
- Activity Logging to MongoDB

## Setup
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000/docs
