from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

DB_NAME = "car_rental.db"

@app.route("/")
def home():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    cars = conn.execute("""
        SELECT id, type, model, color, plate, fuel, status, daily_rate
        FROM cars
    """).fetchall()

    conn.close()

    return render_template("index.html", cars=cars)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
