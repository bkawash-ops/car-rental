from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "car_rental_secret_2026"
DB_NAME = "car_rental.db"


# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INIT DATABASE ----------------
def init_db():
    conn = get_db()

    # USERS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    # CARS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            model TEXT,
            color TEXT,
            plate TEXT,
            fuel TEXT,
            status TEXT,
            daily_rate REAL
        )
    """)

    # CONTRACTS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            car_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            total_price REAL,
            paid_amount REAL DEFAULT 0,
            remaining REAL DEFAULT 0,
            status TEXT
        )
    """)

    # ---------------- DEFAULT USERS ----------------
    users = [
        ("admin", "1234", "admin"),
        ("seller", "1234", "seller")
    ]

    for u in users:
        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                u
            )
        except:
            pass

    # ---------------- DEFAULT CARS (مهم جداً) ----------------
    cars = [
        ("Sedan", "Toyota Corolla", "White", "1111", "Petrol", "Available", 20),
        ("SUV", "Honda CRV", "Black", "2222", "Diesel", "Available", 35),
        ("Hatchback", "Kia Picanto", "Red", "3333", "Petrol", "Available", 15)
    ]

    for c in cars:
        conn.execute("""
            INSERT INTO cars (type, model, color, plate, fuel, status, daily_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, c)

    conn.commit()
    conn.close()


with app.app_context():
    init_db()


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = user["username"]
            session["role"] = user["role"]
            return redirect("/dashboard")

        return "خطأ في البيانات"

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    if session["role"] == "admin":
        return redirect("/")
    return redirect("/contracts")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- HOME (ADMIN ONLY) ----------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/contracts")

    conn = get_db()
    cars = conn.execute("SELECT * FROM cars ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("index.html", cars=cars)


# ---------------- ADD CAR ----------------
@app.route("/add", methods=["POST"])
def add_car():
    conn = get_db()

    conn.execute("""
        INSERT INTO cars (type, model, color, plate, fuel, status, daily_rate)
        VALUES (?, ?, ?, ?, ?, 'Available', ?)
    """, (
        request.form["type"],
        request.form["model"],
        request.form["color"],
        request.form["plate"],
        request.form["fuel"],
        request.form["daily_rate"]
    ))

    conn.commit()
    conn.close()
    return redirect("/")


# ---------------- CONTRACTS ----------------
@app.route("/contracts")
def contracts():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()

    cars = conn.execute("""
        SELECT * FROM cars 
    """).fetchall()

    contracts = conn.execute("""
        SELECT contracts.*,
               cars.model,
               cars.plate,
               (julianday(end_date) - julianday(start_date) + 1) AS days
        FROM contracts
        LEFT JOIN cars ON cars.id = contracts.car_id
        ORDER BY contracts.id DESC
    """).fetchall()

    conn.close()

    return render_template("contracts.html", cars=cars, contracts=contracts)


# ---------------- CREATE CONTRACT ----------------
@app.route("/create_contract", methods=["POST"])
def create_contract():

    conn = get_db()

    total = float(request.form.get("total_price") or 0)
    paid = float(request.form.get("paid_amount") or 0)

    remaining = total - paid

    conn.execute("""
        INSERT INTO contracts 
        (customer_name, customer_phone, car_id, start_date, end_date,
         total_price, paid_amount, remaining, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form["customer_name"],
        request.form["customer_phone"],
        request.form["car_id"],
        request.form["start_date"],
        request.form["end_date"],
        total,
        paid,
        remaining,
        "Active"
    ))

    conn.execute("""
        UPDATE cars SET status='Rented' WHERE id=?
    """, (request.form["car_id"],))

    conn.commit()
    conn.close()

    return redirect("/contracts")
@app.route("/print_contract/<int:id>")
def print_contract(id):

    conn = get_db()

    c = conn.execute("""
        SELECT contracts.*,
               cars.model,
               cars.plate,
               (julianday(end_date)-julianday(start_date)+1) AS days
        FROM contracts
        LEFT JOIN cars ON cars.id = contracts.car_id
        WHERE contracts.id=?
    """, (id,)).fetchone()

    conn.close()

    # 🔴 مهم جداً: حماية من الخطأ
    if c is None:
        return "العقد غير موجود", 404

    return render_template("invoice.html", c=c)
if __name__ == "__main__":
    app.run(debug=True)
