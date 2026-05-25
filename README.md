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
Login: POST /api/accounts/login/
Current user: GET /api/accounts/me/
Products: GET /api/
Sales: /api/sales/
Payments: /api/payments/
M-Pesa STK: POST /api/mpesa-transactions/stk-push/
Reports: /api/reports/summary/
Excel template: /api/excel/template/products/
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
