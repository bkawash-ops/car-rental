from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

DB_NAME = "car_rental.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

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
