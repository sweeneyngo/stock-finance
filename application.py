import os

import sqlite3

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd

import sys
import re


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
conn = sqlite3.connect("finance.db", check_same_thread=False)
db = conn.cursor()


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    db.execute(
        "SELECT symbol, name, shares, price FROM transactions WHERE user_id= ?", (session["user_id"],))
    transactions = db.fetchall()

    db.execute("SELECT cash FROM users WHERE id= ?",
               (session["user_id"],))
    money = db.fetchall()

    # Ensure there's one unique id per user
    if len(money) != 1:
        return apology("Multiple identical user id", 500)

    # Ensure the user has enough money to buy the stock
    userMoney = money[0][0]
    userTotal = money[0][0]

    for transaction in transactions:
        userTotal += (transaction[2] * transaction[3])

    return render_template("index.html", transactions=transactions, userMoney=userMoney, userTotal=userTotal)


@ app.route("/buy", methods=["GET", "POST"])
@ login_required
def buy():

    if request.method == "POST":
        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("invalid symbol", 403)

        if not lookup(request.form.get("symbol")):
            return apology("symbol not found", 404)

        # Ensure shares was submitted
        if not request.form.get("shares") or int(request.form.get("shares")) <= 0:
            return apology("invalid shares", 403)

        quote = lookup(request.form.get("symbol"))
        db.execute("SELECT cash FROM users WHERE id = ?",
                   (session["user_id"],))

        money = db.fetchall()

        # Ensure there's one unique id per user
        if len(money) != 1:
            return apology("Multiple identical user id", 500)

        # Ensure the user has enough money to buy the stock
        if quote['price'] > money[0][0]:
            return apology("Insufficient money.", 500)

        db.execute(
            "CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id NUMERIC NOT NULL, symbol TEXT NOT NULL, name TEXT NOT NULL, shares NUMERIC NOT NULL, price NUMERIC NOT NULL, time TEXT NOT NULL) ")

        db.execute("INSERT INTO transactions (user_id, symbol, name, shares, price, time) VALUES (?, ?, ?, ?, ?, ?)",
                   (session["user_id"], quote["symbol"], quote["name"], request.form.get("shares"), quote["price"], datetime.now()))

        conn.commit()

        # Update remaining cash for user
        newCash = money[0][0] - \
            (quote['price'] * int(request.form.get("shares")))
        db.execute("UPDATE users SET cash = ?WHERE id=?",
                   (newCash, session["user_id"]))

        conn.commit()

        return redirect("/")

    elif request.method == "GET":
        return render_template("buy.html")


@ app.route("/history")
@ login_required
def history():
    db.execute(
        "CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id NUMERIC NOT NULL, symbol TEXT NOT NULL, name TEXT NOT NULL, shares NUMERIC NOT NULL, price NUMERIC NOT NULL, time TEXT NOT NULL) ")
    db.execute(
        "CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id NUMERIC NOT NULL, symbol TEXT NOT NULL, name TEXT NOT NULL, shares NUMERIC NOT NULL, price NUMERIC NOT NULL, time TEXT NOT NULL) ")
    db.execute("SELECT symbol, shares, price, time FROM transactions WHERE id=? UNION ALL SELECT symbol, shares, price, time FROM sales WHERE user_id=? ORDER BY time DESC",
               (session["user_id"], session["user_id"]))
    history = db.fetchall()

    return render_template("history.html", history=history)


@ app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        db.execute("SELECT * FROM users WHERE username = ?",
                   (request.form.get("username"),))

        rows = db.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@ app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@ app.route("/quote", methods=["GET", "POST"])
@ login_required
def quote():

    if request.method == "POST":
        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("invalid symbol", 403)

        if not lookup(request.form.get("symbol")):
            return apology("symbol not found", 404)

        quote = lookup(request.form.get("symbol"))
        res = f"A share of {quote['name']} ({quote['symbol']}) costs ${quote['price']}."
        return render_template("quoted.html", quote=res)

    elif request.method == "GET":
        return render_template("quote.html")


@ app.route("/register", methods=["GET", "POST"])
def register():
  # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("invalid username", 403)

        # Ensure password was submitted
        elif not (request.form.get("password")):
            return apology("invalid password", 403)
        # Ensure confirm was submitted
        elif not (request.form.get("confirm")):
            return apology("invalid confirm", 403)
        # Ensure there's a match
        elif request.form.get("password") != request.form.get("confirm"):
            return apology("invalid match", 403)

        # Query database for username
        db.execute("SELECT * FROM users WHERE username = ?",
                   (request.form.get("username"),))

        rows = db.fetchall()
        # Ensure username doesn't exist
        if len(rows) >= 1:
            return apology("invalid username and/or password", 403)

        # Add user to database

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (request.form.get(
            "username"), generate_password_hash(request.form.get("password"))))

        conn.commit()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@ app.route("/sell", methods=["GET", "POST"])
@ login_required
def sell():
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("no symbol selected", 403)
        # Ensure shares was submitted
        if not request.form.get("shares") or int(request.form.get("shares")) <= 0:
            return apology("invalid shares", 403)
        db.execute("SELECT shares, price FROM transactions WHERE symbol=? AND user_id=? LIMIT 1",
                   (re.sub('[^a-zA-Z]+', '', request.form.get("symbol")), session["user_id"]))

        text = re.sub(
            '[()]', '', str(db.fetchone()))
        arr = text.split(', ')

        print(arr, file=sys.stdout)

        currentShares = arr[0]
        currentPrice = arr[1]
        db.execute("UPDATE transactions SET shares=? WHERE symbol=?",
                   (int(currentShares) - int(request.form.get("shares")),
                    re.sub('[^a-zA-Z]+', '', request.form.get("symbol"))))
        db.execute("DELETE FROM transactions WHERE shares <= 0")

        conn.commit()

        db.execute("SELECT cash FROM users WHERE id= ?",
                   (session["user_id"],))
        money = db.fetchall()

        newCash = money[0][0] + \
            (float(currentPrice) * int(request.form.get("shares")))
        db.execute("UPDATE users SET cash = ?WHERE id=?",
                   (newCash, session["user_id"]))

        db.execute(
            "CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id NUMERIC NOT NULL, symbol TEXT NOT NULL, shares NUMERIC NOT NULL, price NUMERIC NOT NULL, time TEXT NOT NULL) ")

        db.execute("INSERT INTO sales (user_id, symbol, shares, price, time) VALUES (?, ?, ?, ?, ?)",
                   (session["user_id"], re.sub('[^a-zA-Z]+', '', request.form.get("symbol")),
                    request.form.get("shares"), (-1 * float(currentPrice)), datetime.now()))

        conn.commit()

        # Redirect user to home page
        return redirect("/")

    elif request.method == "GET":
        db.execute("SELECT DISTINCT symbol FROM transactions WHERE user_id = ?",
                   (session["user_id"],))
        userSymbols = db.fetchall()
        return render_template("sell.html", userSymbols=userSymbols)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
