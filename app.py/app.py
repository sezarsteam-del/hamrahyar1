
import os
import sqlite3
from functools import wraps
from flask import Flask, request, redirect, session, render_template_string, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")

DB = "hamrahyar.db"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me-now")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0
        )""")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'در انتظار'
        )""")

init_db()

STYLE = """
<style>
*{box-sizing:border-box}
body{margin:0;background:#f3f5fa;color:#20263b;
font-family:Tahoma,Arial,sans-serif;direction:rtl}
header{background:#171d35;color:white;padding:22px 7%;
display:flex;justify-content:space-between;align-items:center}
header h2{margin:0;color:#a99aff}
a{color:inherit;text-decoration:none}
.container{max-width:1100px;margin:35px auto;padding:0 18px}
.hero{background:linear-gradient(120deg,#29234e,#6351b7);
color:white;padding:30px;border-radius:18px;margin-bottom:25px}
.hero h1{margin-top:0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:15px}
.card{background:white;padding:22px;border-radius:15px;
box-shadow:0 5px 20px #1820440b}
.number{font-size:30px;font-weight:bold;color:#7058d5;margin-top:12px}
nav{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}
.btn{display:inline-block;background:#7058d5;color:white;
padding:12px 18px;border:0;border-radius:9px;cursor:pointer}
.btn.dark{background:#292f49}
input{width:100%;padding:13px;border:1px solid #ddd;
border-radius:9px;margin:8px 0 15px;font-size:15px}
table{width:100%;border-collapse:collapse;background:white}
td,th{padding:14px;border-bottom:1px solid #eee;text-align:right}
th{background:#f8f7fc}
form{max-width:500px}
small{color:#777}
@media(max-width:600px){header{padding:18px}
td,th{padding:9px;font-size:13px}}
</style>
"""

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/login")
        return fn(*args, **kwargs)
    return wrapper

LOGIN = """
<!doctype html><html lang="fa"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
""" + STYLE + """
<body><div class="container">
<div class="card">
<h2>ورود به همراه‌یار</h2>
<form method="post">
<label>رمز عبور مدیریت</label>
<input name="password" type="password" required>
<button class="btn">ورود به پنل</button>
</form>
</div></div></body></html>
"""

@app.route("/")
def home():
    if session.get("admin"):
        return redirect("/admin")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        flash("رمز عبور اشتباه است")
    return render_template_string(LOGIN)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/admin")
@login_required
def admin():
    with db() as conn:
        products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status='در انتظار'"
        ).fetchone()[0]
    return render_template_string("""
    <!doctype html><html lang="fa"><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    """ + STYLE + """
    <body>
    <header><h2>همراه‌یار</h2><a href="/logout">خروج</a></header>
    <main class="container">
    <section class="hero">
    <h1>خوش آمدید 👋</h1>
    <p>پنل مدیریت هوشمند کسب‌وکار شما</p>
    </section>
    <div class="cards">
    <div class="card">کل محصولات<div class="number">{{p}}</div></div>
    <div class="card">کل سفارش‌ها<div class="number">{{o}}</div></div>
    <div class="card">سفارش‌های در انتظار<div class="number">{{w}}</div></div>
    </div>
    <nav>
    <a class="btn" href="/products">مدیریت محصولات</a>
    <a class="btn dark" href="/orders">مدیریت سفارش‌ها</a>
    </nav>
    <div class="card"><h3>به همراه‌یار خوش آمدید</h3>
    <small>مدیریت محصولات و سفارش‌های فروشگاه از یک پنل ساده</small></div>
    </main></body></html>
    """, p=products, o=orders, w=pending)

@app.route("/products", methods=["GET", "POST"])
@login_required
def products_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "0")
        stock = request.form.get("stock", "0")
        if name:
            try:
                with db() as conn:
                    conn.execute(
                        "INSERT INTO products(name,price,stock) VALUES(?,?,?)",
                        (name, float(price), int(stock))
                    )
            except ValueError:
                pass
        return redirect("/products")

    with db() as conn:
        items = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()

    return render_template_string("""
    <!doctype html><html lang="fa"><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    """ + STYLE + """
    <body><header><h2>محصولات همراه‌یار</h2><a href="/admin">داشبورد</a></header>
    <main class="container">
    <div class="card"><h3>افزودن محصول</h3>
    <form method="post">
    <input name="name" placeholder="نام محصول" required>
    <input name="price" type="number" step="0.01" placeholder="قیمت" required>
    <input name="stock" type="number" placeholder="موجودی" required>
    <button class="btn">ثبت محصول</button>
    </form></div>
    <h3>فهرست محصولات</h3>
    <div class="card"><table>
    <tr><th>نام</th><th>قیمت</th><th>موجودی</th><th>حذف</th></tr>
    {% for x in items %}
    <tr><td>{{x.name}}</td><td>{{x.price}}</td><td>{{x.stock}}</td>
    <td><a href="/delete-product/{{x.id}}">حذف</a></td></tr>
    {% endfor %}
    </table></div></main></body></html>
    """, items=items)

@app.route("/delete-product/<int:pid>")
@login_required
def delete_product(pid):
    with db() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (pid,))
    return redirect("/products")

@app.route("/orders", methods=["GET", "POST"])
@login_required
def orders_page():
    if request.method == "POST":
        customer = request.form.get("customer", "").strip()
        product = request.form.get("product", "").strip()
        if customer and product:
            with db() as conn:
                conn.execute(
                    "INSERT INTO orders(customer,product) VALUES(?,?)",
                    (customer, product)
                )
        return redirect("/orders")

    with db() as conn:
        items = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()

    return render_template_string("""
    <!doctype html><html lang="fa"><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    """ + STYLE + """
    <body><header><h2>سفارش‌های همراه‌یار</h2><a href="/admin">داشبورد</a></header>
    <main class="container">
    <div class="card"><h3>ثبت سفارش</h3>
    <form method="post">
    <input name="customer" placeholder="نام مشتری" required>
    <input name="product" placeholder="نام محصول" required>
    <button class="btn">ثبت سفارش</button>
    </form></div>
    <h3>فهرست سفارش‌ها</h3>
    <div class="card"><table>
    <tr><th>مشتری</th><th>محصول</th><th>وضعیت</th></tr>
    {% for x in items %}
    <tr><td>{{x.customer}}</td><td>{{x.product}}</td><td>{{x.status}}</td></tr>
    {% endfor %}
    </table></div></main></body></html>
    """, items=items)

@app.route("/health")
def health():
    return {"status": "ok", "app": "Hamrahyar"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
