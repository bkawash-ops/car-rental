from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

DB_NAME = "car_rental.db"

# ✅ أولاً: تعريف get_db
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ❗ إنشاء جدول العقود (بعد تعريف get_db)
with app.app_context():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            car_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            total_price REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_db()
    cars = conn.execute("SELECT * FROM cars").fetchall()
    conn.close()
    return render_template("index.html", cars=cars)


@app.route("/add", methods=["POST"])
def add_car():
    conn = get_db()
    conn.execute("""
        INSERT INTO cars (type, model, color, plate, fuel, status, daily_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form["type"],
        request.form["model"],
        request.form["color"],
        request.form["plate"],
        request.form["fuel"],
        request.form["status"],
        request.form["daily_rate"]
    ))
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/delete/<int:car_id>")
def delete_car(car_id):
    conn = get_db()
    conn.execute("DELETE FROM cars WHERE id = ?", (car_id,))
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/contracts")
def contracts():
    conn = get_db()

    # السيارات المتاحة فقط
    cars = conn.execute("""
        SELECT * FROM cars WHERE status='Available'
    """).fetchall()

    # العقود + حساب الأيام داخل SQL
    contracts = conn.execute("""
        SELECT contracts.*,
               cars.model,
               cars.plate,
               (julianday(end_date) - julianday(start_date)) AS days
        FROM contracts
        LEFT JOIN cars ON cars.id = contracts.car_id
        ORDER BY contracts.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "contracts.html",
        cars=cars,
        contracts=contracts
    )


@app.route("/create_contract", methods=["POST"])
def create_contract():
    conn = get_db()

    conn.execute("""
        INSERT INTO contracts 
        (customer_name, customer_phone, car_id, start_date, end_date, total_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form["customer_name"],
        request.form["customer_phone"],
        request.form["car_id"],
        request.form["start_date"],
        request.form["end_date"],
        request.form["total_price"],
        "Active"
    ))

    conn.execute("UPDATE cars SET status='Rented' WHERE id=?",
                 (request.form["car_id"],))

    conn.commit()
    conn.close()
    return redirect("/contracts")
