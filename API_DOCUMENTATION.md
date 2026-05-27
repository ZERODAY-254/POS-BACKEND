# POS Backend API Documentation

Last verified: 2026-05-26

## Base URL

Local development:

```text
http://127.0.0.1:8000/api
```

## Postman Collection

Import these two files into Postman:

```text
C:\Users\Alfred\OneDrive\Desktop\POS_BACKEND\backend\postman_collection.json
C:\Users\Alfred\OneDrive\Desktop\POS_BACKEND\backend\postman_environment.json
```

After importing:

1. Select the `POS Backend Local` environment.
2. Open the environment and set the `password` value.
3. Run `Authentication > Login`.
4. The login test automatically saves `access_token` and `refresh_token`.
5. Run the other requests.

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

## Authentication

Most API endpoints require a JWT access token.

### Login

```http
POST /api/accounts/login/
Content-Type: application/json
```

Body:

```json
{
  "username": "ALFRED",
  "password": "your-password"
}
```

Successful response:

```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "ALFRED",
    "role": "admin"
  },
  "two_factor_required": false,
  "tokens": {
    "access": "JWT_ACCESS_TOKEN",
    "refresh": "JWT_REFRESH_TOKEN"
  }
}
```

Use the access token on protected requests:

```http
Authorization: Bearer JWT_ACCESS_TOKEN
```

### Current User

```http
GET /api/accounts/me/
```

### Refresh Token

```http
POST /api/accounts/token/refresh/
Content-Type: application/json
```

Body:

```json
{
  "refresh": "JWT_REFRESH_TOKEN"
}
```

### Register User

```http
POST /api/accounts/register/
```

### Two-Factor Verification

```http
POST /api/accounts/two-factor/verify/
```

### Password Reset

```http
POST /api/accounts/password-reset/request/
POST /api/accounts/password-reset/confirm/
```

## Product Management

### Products

```http
GET /api/products/
GET /api/products/?search=laptop
POST /api/products/
GET /api/products/{product_id}/
PUT /api/products/{product_id}/
DELETE /api/products/{product_id}/
POST /api/add/
PUT /api/update/{product_id}/
DELETE /api/delete/{product_id}/
```

Both `POST /api/products/` and `POST /api/products` are supported for Postman.

Create/update product example:

```json
{
  "name": "HP EliteBook",
  "description": "Business laptop",
  "category": 1,
  "supplier": 1,
  "sku": "HP-ELITE-001",
  "barcode": "1234567890",
  "cost_price": "45000.00",
  "price": "55000.00",
  "wholesale_price": "52000.00",
  "quantity": 10,
  "minimum_stock": 2,
  "is_active": true
}
```

### Categories, Suppliers, Units, Tax

```http
GET /api/categories/
GET /api/suppliers/
GET /api/units/
GET /api/unit-conversions/
GET /api/conversion-preview/
GET /api/tax-codes/
GET /api/stock-alerts/
```

## Inventory

Inventory endpoints are available in two places:

```http
GET /api/inventory/movements/
POST /api/inventory/adjust/
```

Separate inventory app routes:

```http
GET /api/inventory-app/movements/
POST /api/inventory-app/adjust/
GET /api/inventory-app/stock-alerts/
GET /api/inventory-app/suppliers/
GET /api/inventory-app/units/
GET /api/inventory-app/unit-conversions/
GET /api/inventory-app/conversion-preview/
```

## Sales & POS

```http
GET /api/sales/
POST /api/sales/
GET /api/sales/{id}/
PUT /api/sales/{id}/
DELETE /api/sales/{id}/
GET /api/sales/{id}/receipt/
GET /api/sales/{id}/print-receipt/
GET /api/sales/{id}/invoice/
GET /api/sales/{id}/print-invoice/
GET /api/sales/daily-report/
GET /api/sales/dashboard/
```

Create sale example:

```json
{
  "customer_name": "Walk-in Customer",
  "amount": "1160.00",
  "subtotal": "1000.00",
  "discount": "0.00",
  "tax": "160.00",
  "grand_total": "1160.00",
  "amount_paid": "1200.00",
  "payment_method": "cash",
  "payment_status": "paid",
  "items": [
    {
      "product_id": 1,
      "name": "Test Item",
      "sku": "SKU1",
      "barcode": "BAR1",
      "price": 1000,
      "quantity": 1
    }
  ]
}
```

Receipts and invoice numbers are generated automatically when a sale is saved.

## Customers

```http
GET /api/customers/
POST /api/customers/
GET /api/customers/{id}/
PUT /api/customers/{id}/
DELETE /api/customers/{id}/
```

## Payments

```http
GET /api/payments/
POST /api/payments/
GET /api/payments/{id}/
PUT /api/payments/{id}/
DELETE /api/payments/{id}/
GET /api/cash-drawers/
GET /api/cash-drawer-transactions/
GET /api/payment-notifications/
```

## M-Pesa

Main payment routes:

```http
GET /api/mpesa/health/
GET /api/mpesa/callback-config/
POST /api/mpesa/callback/
GET /api/mpesa-transactions/
```

Separate M-Pesa app routes:

```http
GET /api/mpesa-app/health/
GET /api/mpesa-app/callback-config/
POST /api/mpesa-app/callback/
GET /api/mpesa-app/transactions/
```

Important: real STK confirmation requires a public callback URL. A placeholder callback URL will not receive Safaricom callbacks.

## Returns

```http
GET /api/returns/
POST /api/returns/
GET /api/returns/{id}/
PUT /api/returns/{id}/
DELETE /api/returns/{id}/
```

## Orders

```http
GET /api/orders/
POST /api/orders/
GET /api/orders/{id}/
PUT /api/orders/{id}/
DELETE /api/orders/{id}/
```

## Reports & Dashboard

General report routes:

```http
GET /api/reports/summary/
GET /api/reports/sales/
GET /api/reports/inventory/
GET /api/reports/payments/
GET /api/dashboard/charts/
GET /api/react/payment-config/
```

Separate reports app routes:

```http
GET /api/reports-app/summary/
GET /api/reports-app/sales/
GET /api/reports-app/inventory/
GET /api/reports-app/payments/
GET /api/reports-app/charts/
```

## Excel Import and Export

```http
GET /api/excel/template/products/
GET /api/excel/export/products/
GET /api/excel/export/inventory/
GET /api/excel/export/sales/
POST /api/excel/import/products/
```

The product import endpoint expects an uploaded Excel file.

## Notifications

```http
GET /api/notifications/
POST /api/notifications/
GET /api/notifications/{id}/
PUT /api/notifications/{id}/
DELETE /api/notifications/{id}/
GET /api/notifications/bot/status/
POST /api/notifications/bot/run/
```

Notification bot command:

```powershell
python manage.py run_notification_bot
```

## System Configuration

```http
GET /api/branches/
POST /api/branches/
GET /api/terminals/
POST /api/terminals/
POST /api/terminals/heartbeat/
GET /api/approvals/
POST /api/approvals/
POST /api/approvals/{approval_id}/decide/
GET /api/offline-sync/
POST /api/offline-sync/
```

## Audit Logs

```http
GET /api/audit-logs/
GET /api/audit-logs/{id}/
```

## Verified Endpoint Status

The following checks passed using authenticated API requests:

```text
POST /api/accounts/login/ -> 200 OK
GET /api/accounts/me/ -> 200 OK
GET /api/categories/ -> 200 OK
GET /api/products/ -> 200 OK
GET /api/suppliers/ -> 200 OK
GET /api/units/ -> 200 OK
GET /api/tax-codes/ -> 200 OK
GET /api/stock-alerts/ -> 200 OK
GET /api/inventory/movements/ -> 200 OK
GET /api/sales/ -> 200 OK
GET /api/sales/dashboard/ -> 200 OK
GET /api/sales/daily-report/ -> 200 OK
GET /api/customers/ -> 200 OK
GET /api/payments/ -> 200 OK
GET /api/mpesa/health/ -> 200 OK
GET /api/mpesa/callback-config/ -> 200 OK
GET /api/returns/ -> 200 OK
GET /api/orders/ -> 200 OK
GET /api/audit-logs/ -> 200 OK
GET /api/reports/summary/ -> 200 OK
GET /api/reports/sales/ -> 200 OK
GET /api/reports/inventory/ -> 200 OK
GET /api/reports/payments/ -> 200 OK
GET /api/dashboard/charts/ -> 200 OK
GET /api/react/payment-config/ -> 200 OK
GET /api/branches/ -> 200 OK
GET /api/terminals/ -> 200 OK
GET /api/approvals/ -> 200 OK
GET /api/offline-sync/ -> 200 OK
GET /api/notifications/ -> 200 OK
GET /api/notifications/bot/status/ -> 200 OK
GET /api/mpesa-app/health/ -> 200 OK
GET /api/mpesa-app/transactions/ -> 200 OK
GET /api/reports-app/summary/ -> 200 OK
GET /api/inventory-app/stock-alerts/ -> 200 OK
```

Backend system check:

```text
python manage.py check -> System check identified no issues
```

## Quick Manual Test

Start backend:

```powershell
cd C:\Users\Alfred\OneDrive\Desktop\POS_BACKEND\backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

Login test:

```powershell
$body = @{ username='ALFRED'; password='your-password' } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/accounts/login/ -Method POST -Body $body -ContentType 'application/json'
```

Authenticated API test:

```powershell
$token = '<ACCESS_TOKEN_FROM_LOGIN>'
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/sales/dashboard/ -Headers @{ Authorization = "Bearer $token" }
```
