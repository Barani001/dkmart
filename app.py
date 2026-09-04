"""
DK MART - Retail Billing & Management System
Author: DHIVAKAR S
"""

import os
import sqlite3
import smtplib
from email.message import EmailMessage
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

# --- SMTP / EMAIL CONFIGURATION ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("shop_system.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total_price REAL NOT NULL,
            date TEXT NOT NULL,
            cashier TEXT NOT NULL
        )
    """)
    
    # Default Admin Account
    cursor.execute("SELECT * FROM users WHERE role='Admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", generate_password_hash("admin123"), "Admin"))
    
    # Populate Full 40 Item Catalog if empty
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        inventory_items = [
            ("Aashirvaad Atta 5kg", 310.00, 25),
            ("India Gate Basmati Rice 5kg", 520.00, 18),
            ("Sugar 1kg", 48.00, 60),
            ("Toor Dal 1kg", 165.00, 35),
            ("Moong Dal 1kg", 145.00, 30),
            ("Fortune Sunflower Oil 1L", 145.00, 40),
            ("Gold Winner Oil 1L", 175.00, 32),
            ("Tata Salt 1kg", 30.00, 75),
            ("Red Label Tea 250g", 125.00, 28),
            ("Bru Coffee 100g", 210.00, 20),
            ("Nescafé Classic 100g", 310.00, 15),
            ("Milk 1L", 60.00, 50),
            ("Curd 500g", 40.00, 35),
            ("Amul Butter 100g", 60.00, 25),
            ("Amul Cheese 200g", 145.00, 18),
            ("Bread 400g", 45.00, 30),
            ("Eggs", 7.00, 120),
            ("Maggi Noodles 70g", 15.00, 100),
            ("Lay's Chips 50g", 30.00, 55),
            ("Bingo Chips 50g", 30.00, 45),
            ("Oreo 120g", 40.00, 40),
            ("Parle-G 250g", 25.00, 70),
            ("Good Day 150g", 40.00, 45),
            ("Dairy Milk 40g", 45.00, 35),
            ("KitKat 45g", 50.00, 30),
            ("Coca-Cola 750ml", 45.00, 40),
            ("Pepsi 750ml", 45.00, 35),
            ("Sprite 750ml", 45.00, 30),
            ("Mineral Water 1L", 20.00, 100),
            ("Vim Dishwash Bar", 25.00, 40),
            ("Surf Excel 1kg", 175.00, 22),
            ("Harpic 500ml", 110.00, 25),
            ("Dettol Handwash 250ml", 95.00, 20),
            ("Lux Soap 100g", 38.00, 50),
            ("Dove Soap 100g", 65.00, 30),
            ("Clinic Plus Shampoo 175ml", 110.00, 18),
            ("Colgate Toothpaste 150g", 115.00, 25),
            ("Toothbrush", 40.00, 40),
            ("Coconut Oil 200ml", 90.00, 20),
            ("Matchbox", 2.00, 150)
        ]
        cursor.executemany("INSERT INTO inventory (name, price, stock) VALUES (?, ?, ?)", inventory_items)
        
    conn.commit()
    conn.close()

init_db()

# --- HELPER: SEND EMAIL RECEIPT ---
def send_email_receipt(recipient_email, customer_name, receipt_id, filepath):
    if not recipient_email or "@" not in recipient_email:
        return False, "Invalid email address."
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Invoice Receipt #{receipt_id} - DK MART"
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        body = f"Dear {customer_name if customer_name else 'Valued Customer'},\n\nThank you for shopping at DK MART!\n\nAttached is your official PDF invoice receipt (#{receipt_id}).\n\nBest regards,\nDK MART Team\nAuthorized Signature: BARANIDHARAN S\n"
        msg.set_content(body)

        with open(filepath, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(filepath))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Email delivery failed: {str(e)}"

# --- PDF GENERATOR ---
def generate_pdf_receipt(receipt_id, customer_name, items, grand_total, cashier_name, output_filename):
    doc = SimpleDocTemplate(output_filename, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#0F172A'))
    subtitle_style = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#475569'))
    right_text = ParagraphStyle('RightText', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, alignment=2, textColor=colors.HexColor('#334155'))

    header_data = [
        [
            Paragraph("<b>DK MART</b><br/><font size=9 color='#64748B'>123 Commercial Plaza, Suite 400<br/>Phone: +91 98765 43210 | Email: billing@dkmart.com</font>", title_style),
            Paragraph(f"<b>OFFICIAL INVOICE</b><br/>Invoice #: <b>{receipt_id}</b><br/>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", right_text)
        ]
    ]
    header_table = Table(header_data, colWidths=[320, 200])
    header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=15))

    meta_data = [[
        Paragraph(f"<b>Customer:</b> {customer_name if customer_name else 'Valued Customer'}", subtitle_style),
        Paragraph(f"<b>Cashier:</b> {cashier_name}", right_text)
    ]]
    meta_table = Table(meta_data, colWidths=[300, 220])
    meta_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    table_data = [["Item Description", "Price (₹)", "Qty", "Total (₹)"]]
    for item in items:
        table_data.append([item['name'], f"Rs.{item['price']:.2f}", str(item['qty']), f"Rs.{item['total']:.2f}"])

    item_table = Table(table_data, colWidths=[260, 80, 60, 120])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 15))

    summary_data = [["Subtotal:", f"Rs.{grand_total:.2f}"], ["Tax (0%):", "Rs.0.00"], ["Grand Total:", f"Rs.{grand_total:.2f}"]]
    summary_table = Table(summary_data, colWidths=[400, 120])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, -1), (1, -1), colors.HexColor('#0F172A')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 25))

    sig_data = [["", "Authorized Signature"], ["", "BARANIDHARAN S"]]
    sig_table = Table(sig_data, colWidths=[320, 200])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('LINEABOVE', (1, 0), (1, 0), 1, colors.HexColor('#475569')),
        ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=10))

    footer_style = ParagraphStyle('FooterText', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, alignment=1, textColor=colors.HexColor('#94A3B8'))
    story.append(Paragraph("Thank you for shopping at DK MART!", footer_style))
    doc.build(story)

# --- ROUTES ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        conn = sqlite3.connect("shop_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, role FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            session["user"] = user[0]
            session["role"] = user[2]
            return redirect(url_for("admin") if user[2] == "Admin" else url_for("billing"))
        return render_template("login.html", error="Invalid username or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/billing")
def billing():
    if "user" not in session: return redirect(url_for("login"))
    conn = sqlite3.connect("shop_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    conn.close()
    return render_template("billing.html", items=items, user=session["user"], role=session["role"])

@app.route("/admin")
def admin():
    if session.get("role") != "Admin": return redirect(url_for("billing"))
    conn = sqlite3.connect("shop_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_price), COUNT(id) FROM sales")
    total_rev, total_sales = cursor.fetchone()
    total_rev = total_rev if total_rev else 0.0
    total_sales = total_sales if total_sales else 0

    cursor.execute("SELECT date, SUM(total_price) FROM sales GROUP BY date ORDER BY id DESC LIMIT 7")
    chart_data = cursor.fetchall()
    
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    conn.close()

    dates = [r[0] for r in reversed(chart_data)]
    revenues = [r[1] for r in reversed(chart_data)]

    return render_template("admin.html", user=session["user"], total_rev=total_rev, total_sales=total_sales, dates=dates, revenues=revenues, items=items)

@app.route("/api/add_staff", methods=["POST"])
def add_staff():
    if session.get("role") != "Admin": return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    try:
        conn = sqlite3.connect("shop_system.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'Staff')", (data['username'], generate_password_hash(data['password'])))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Staff '{data['username']}' created successfully!"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists."})

@app.route("/api/manage_item", methods=["POST"])
def manage_item():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    action = data.get("action")
    conn = sqlite3.connect("shop_system.db")
    cursor = conn.cursor()
    try:
        if action == "add":
            cursor.execute("INSERT INTO inventory (name, price, stock) VALUES (?, ?, ?)", (data['name'], float(data['price']), int(data['stock'])))
        elif action == "edit":
            cursor.execute("UPDATE inventory SET name=?, price=?, stock=? WHERE id=?", (data['name'], float(data['price']), int(data['stock']), int(data['id'])))
        elif action == "delete":
            cursor.execute("DELETE FROM inventory WHERE id=?", (int(data['id']),))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/checkout", methods=["POST"])
def checkout():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    cart = data.get("cart", [])
    cust_name = data.get("customer", "").strip()
    cust_email = data.get("email", "").strip()
    cust_phone = data.get("phone", "").strip()

    if not cart: return jsonify({"success": False, "message": "Cart is empty."})

    receipt_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    grand_total = sum(i['total'] for i in cart)
    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect("shop_system.db")
    cursor = conn.cursor()
    for item in cart:
        cursor.execute("INSERT INTO sales (receipt_id, item_name, quantity, price, total_price, date, cashier) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (receipt_id, item['name'], item['qty'], item['price'], item['total'], today, session["user"]))
        cursor.execute("UPDATE inventory SET stock = stock - ? WHERE id = ?", (item['qty'], item['id']))
    conn.commit()
    conn.close()

    os.makedirs("invoices", exist_ok=True)
    filename = f"Receipt_{receipt_id}.pdf"
    filepath = os.path.join("invoices", filename)
    generate_pdf_receipt(receipt_id, cust_name, cart, grand_total, session["user"], filepath)

    email_status = "Not requested"
    if cust_email:
        success, msg = send_email_receipt(cust_email, cust_name, receipt_id, filepath)
        email_status = msg

    wa_url = ""
    if cust_phone:
        clean_phone = "".join(filter(str.isdigit, cust_phone))
        items_summary = "%0A".join([f"• {i['name']} (x{i['qty']}): ₹{i['total']:.2f}" for i in cart])
        pdf_public_url = request.host_url.rstrip('/') + url_for('download_invoice', filename=filename)
        
        wa_text = f"Hello {cust_name if cust_name else 'Valued Customer'}! 👋%0A%0AThank you for shopping at *DK MART*!%0A%0A*Invoice Receipt:* #{receipt_id}%0A*Total Amount:* ₹{grand_total:.2f}%0A%0A*Purchased Items:*%0A{items_summary}%0A%0A📄 *Download PDF Receipt:*%0A{pdf_public_url}"
        wa_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={wa_text}"

    return jsonify({
        "success": True,
        "pdf_url": url_for("download_invoice", filename=filename),
        "whatsapp_url": wa_url,
        "email_status": email_status
    })

@app.route("/invoices/<filename>")
def download_invoice(filename):
    if "user" not in session:
        return redirect(url_for("login"))
    return send_from_directory("invoices", filename)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)