from flask import Flask, render_template, request, redirect, session
import sqlite3 as sql

app = Flask(__name__)
connection = sql.connect('stock.db', check_same_thread=False)
cursor = connection.cursor()


@app.route('/')
def index():

    # Display data of all current stock that current user currently owns, number of shares of each, current price, and total value of holding
    # Display user's current cash balance

    # rows = cursor.execute('SELECT name, email FROM registrants').fetchall()
    # if not rows:
    #     return render_template('error.html')
    # return render_template('index.html', rows=rows)


@app.route('/buy', methods=['GET', 'POST'])
def buy():

    # When requested via GET, display FORM to buy a stock
    # When form is submitted via POST, purchase the stock so long as user can afford it

    # if request.method == 'GET':
    #     return render_template('register.html')
    # elif request.method == 'POST':
    #     name = request.form.get('name')
    #     email = request.form.get('email')

    #     if not name:
    #         return render_template('apology.html', message='You must provide a name. ')
    #     if not email:
    #         return render_template('apology.html', message='You must provide a email. ')

    #     cursor.execute(
    #         'INSERT INTO registrants (name, email) VALUES (:name, :email)', name=name, email=email)
    #     return redirect('/')


@app.route('/history', methods=['GET', 'POST'])
def history():
    # Display table with history of all transactions, listing row by row every buy and every sell

    return


@app.route('/login', methods=['GET', 'POST'])
def login():
    ## Log user in ##
    session.clear()  # remove user ID

    if request.method == 'POST':

        if not request.form.get('username'):
            return apology('must provide username')
        elif not request.form.get('password'):
            return apology('must provide password')

        # Query database for username
        rows = cursor.execute(
            'SELECT * FROM users WHERE username = :username', username=request.form.get('username'))

        # Ensure username exist (must be present, and the password hash matches with password)
        if len(rows) != 1 or not check_password_hash(rows[0]['hash'], request.form.get('password')):
            return apology('invalid username and/or password', 403)

        # Rember which user has logged in
        # should only be one row in rows (one username per acc)
        session['user_id'] = rows[0]['id']

        # Redirect user to homepage
        return redirect('/')

    if request.method == 'GET':
        return render_template('login.html')


@app.route('/logout')
def logout():

    # Forget user_id
    session.clear()
    return redirect('/')


@app.route('/quote', methods=['GET', 'POST'])
@login_required
def quote():
    # Get stock quote
    # When requested via GET, display form to request a stock quote
    # When form submitted via POST, lookup stockup symbol using lookup function, and display the results
    # If given an invalid value, lookup should return None -> display error message -> "doesn't exist"
    return apology('TODO')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # When requested via GET, display registration form
    # When form is submitted via POST, insert new user to users table
    # Be sure to check for invalid inputs, and hash the user's password (don't store actual password)
    return apology('TODO')


@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    # When requested via GET, display form to sell a stock
    # When form submitted via POST, sell specified number of shares of stock, and update user's cash

    # Check for errors

    return apology('TODO')


def errorhandler(e):
    # Handle error
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Personal touch requisite

# Allow users to change password
# Allow users to add cash
# Allow buying or selling stock from index page
# Add password complexity requirements
