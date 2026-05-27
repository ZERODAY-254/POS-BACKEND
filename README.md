# POS Backend API

Django REST backend for a POS and inventory system with MySQL, JWT authentication, M-Pesa STK Push, reports, Excel import/export, inventory tracking, approvals, branches, terminals, and role-based access.

## Requirements

- Python 3.12 or newer
- MySQL Server / MySQL Workbench
- Virtual environment recommended

## Setup

```powershell
cd C:\Users\Alfred\OneDrive\Desktop\POS_BACKEND\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Environment

Create or update `.env`:

```env
DATABASE_ENGINE=mysql
MYSQL_DATABASE=sells_db
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306

MPESA_ENVIRONMENT=sandbox
MPESA_DEMO_MODE=False
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://your-real-domain.com/api/mpesa/callback/
```

## Main URLs

```text
Admin: http://127.0.0.1:8000/admin/
API base: http://127.0.0.1:8000/api/
Health: GET /api/health/
Endpoint list: GET /api/endpoints/
Login: POST /api/auth/login/
Current user: GET /api/auth/me/
Products: GET /api/products/
Categories: GET /api/products/categories/
Sales: /api/sales/
Payments: /api/payments/
M-Pesa STK: POST /api/mpesa-transactions/stk-push/
Reports: /api/reports/summary/
Excel template: /api/excel/template/products/
Automatic Excel status: /api/excel/automatic/
Rebuild automatic Excel files: POST /api/excel/automatic/rebuild/
```

Use JWT tokens with:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Health Check

```powershell
python manage.py check
python manage.py migrate --check
```

## Automatic Excel Files

The backend keeps Excel workbooks updated automatically when records are saved in the database.

Generated files are stored locally in:

```text
backend/exports/
```

The folder is ignored by Git because it contains generated runtime data.

Supported automatic files:

```text
products.xlsx
sales.xlsx
customers.xlsx
payments.xlsx
mpesa_transactions.xlsx
inventory_movements.xlsx
```

Rebuild all Excel files manually:

```powershell
python manage.py sync_excel_exports
```

Rebuild one file:

```powershell
python manage.py sync_excel_exports products
```

Postman endpoints:

```http
GET  http://127.0.0.1:8000/api/excel/automatic/
POST http://127.0.0.1:8000/api/excel/automatic/rebuild/
GET  http://127.0.0.1:8000/api/excel/automatic/products/download/
GET  http://127.0.0.1:8000/api/excel/automatic/sales/download/
```

## Create A Postman Test User

```powershell
python manage.py seed_demo_user
```

Then login in Postman:

```http
POST http://127.0.0.1:8000/api/auth/login/
Content-Type: application/json

{
  "username": "manager",
  "password": "Manager@12345"
}
```

Copy `tokens.access` from the response and use it as:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```
