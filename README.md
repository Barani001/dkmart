# DK MART — Retail Billing & Management System

A Flask-based retail billing and inventory management application with role-based login, inventory management, sales analytics, PDF invoices, email receipts, and WhatsApp receipt sharing.

## Features

- Admin and staff login
- Product inventory management
- Billing/cart workflow
- Sales and revenue dashboard
- PDF invoice generation
- Optional email receipt delivery
- WhatsApp receipt sharing
- Barcode/QR camera scanning support
- SQLite database
- Responsive dark UI using Tailwind CSS

## Tech Stack

- Python
- Flask
- SQLite
- ReportLab
- HTML/CSS/JavaScript
- Tailwind CSS
- Chart.js
- html5-qrcode
- Gunicorn

## Local Setup

```bash
git clone <your-repository-url>
cd <repository-folder>
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

### Demo login

The current source initializes an admin account with:

- Username: `admin`
- Password: `admin123`

**Change this before deploying publicly.**

## Deployment

This is a Flask server application, so GitHub Pages is **not** the correct runtime host. GitHub can host the source repository, while a Python-capable service runs the Flask app.

The repository includes `requirements.txt`, `Procfile`, and `runtime.txt` to simplify deployment on compatible Python hosts.

## Security before public deployment

Do not commit:

- real Gmail/app passwords
- `.env` files
- production database files
- generated invoices
- real customer information

The current application stores passwords as plain text and contains a hard-coded Flask secret key. These should be replaced with environment variables and password hashing before production use.

## Project Structure

```text
DK-MART/
├── app.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   ├── login.html
│   ├── billing.html
│   └── admin.html
└── static/
```


## Free Render deployment

1. Push this repository to GitHub.
2. In Render, create a Web Service from the repository, or use the included `render.yaml`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Set `SECRET_KEY` (Render can generate it) and optional SMTP variables in the Render Environment settings.

### Demo login

- Username: `admin`
- Password: `admin123`

**Change the default admin password before using this for real business data.**

### Important database note

This version uses SQLite for simplicity. Free cloud web-service filesystems are not a reliable permanent database, so sales/inventory data may be lost after a redeploy/restart. For production use, migrate the app to PostgreSQL or another persistent database.
