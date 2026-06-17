# Restaurant Inventory System

A full-stack web application for managing restaurant inventory with AI-powered receipt parsing.

## Features

- **Receipt OCR** — Upload receipt images (JPG, PNG, WEBP) or PDFs; Claude AI extracts items, quantities, units, and prices automatically
- **Inventory Management** — Full CRUD for inventory items with categories, units, and cost tracking
- **Low Stock Alerts** — Visual warnings when items fall below configurable thresholds
- **Sales Tracking** — Record sales that automatically deduct from inventory
- **Dashboard** — At-a-glance stats: total items, total value, low stock count, recent activity

## Stack

| Layer    | Technology                            |
|----------|---------------------------------------|
| Backend  | Python · FastAPI · SQLAlchemy · SQLite |
| AI       | Anthropic Claude (`claude-haiku-4-5`) |
| Frontend | React 18 (CDN) · Tailwind CSS (CDN) · Babel Standalone · Axios |

## Setup & Run

### Prerequisites

- Python 3.9+
- An [Anthropic API key](https://console.anthropic.com/)

### Start the backend

```bash
export ANTHROPIC_API_KEY=your_key_here
./start.sh
```

This will:
1. Create a Python virtual environment inside `backend/.venv`
2. Install all dependencies from `backend/requirements.txt`
3. Start the FastAPI server on `http://localhost:8000`

### Open the frontend

Open `frontend/index.html` directly in your browser (no build step needed).

## Project Structure

```
.
├── backend/
│   ├── main.py          # FastAPI app with all API routes
│   ├── database.py      # SQLAlchemy models (InventoryItem, Receipt, Sale)
│   ├── schemas.py       # Pydantic request/response schemas
│   └── requirements.txt
├── frontend/
│   └── index.html       # Single-file React app (CDN deps, no build tool)
├── start.sh             # Start script
└── README.md
```

## API Endpoints

| Method | Path                       | Description                              |
|--------|----------------------------|------------------------------------------|
| POST   | `/api/receipts/parse`      | Upload receipt image/PDF, get parsed items |
| POST   | `/api/receipts/confirm`    | Confirm parsed items, update inventory  |
| GET    | `/api/inventory`           | List all inventory items                 |
| POST   | `/api/inventory`           | Create inventory item                    |
| PUT    | `/api/inventory/{id}`      | Update inventory item                    |
| DELETE | `/api/inventory/{id}`      | Delete inventory item                    |
| POST   | `/api/sales`               | Record a sale (deducts inventory)        |
| GET    | `/api/sales`               | List recent sales                        |
| GET    | `/api/dashboard`           | Dashboard statistics                     |

Interactive API docs are available at `http://localhost:8000/docs` when the server is running.
