from flask import Flask
from flask.ext.bcrypt import Bcrypt
from flask_mysqldb import MySQL
from flaskext.mysql import MySQL
from flask import Flask, render_template, redirect, url_for, request
import re
from werkzeug.security import generate_password_hash, check_password_hash


mysql = MySQL()
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'gocubs_1'
app.config['MYSQL_DATABASE_DB'] = 'DMS'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

@app.route("/")
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connect().cursor()
        cursor.execute("SELECT PASSWORD from User where EMAIL_ID='" + username + "'")
        data = cursor.fetchone()
        if data is None:
            error = 'Invalid Credentials. Please try again.'
        elif bcrypt.check_password_hash(data[0], password):
            return redirect(url_for('home'))
        else:
            error = 'Invalid Credentials. Please try again.'

    return render_template('login.html', error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        password = request.form['password']
        validation = request.form['workercode']
        
        
        workerind = 'N'
        
        if validation == "123193":
            workerind = 'Y'
        
        db = mysql.connect()
        cursor = db.cursor()
        pass_length = len(password)
        
        
        cursor.execute("SELECT * from User where EMAIL_ID='" + username + "'")
        data = cursor.fetchone()
        
        if len(firstname) > 0 and len(lastname) > 0:
            if re.match(r"[^@]+@[^@]+\.[^@]+", username) or len(username) > 0:
                if pass_length > 5 and pass_length < 13:
                    password = bcrypt.generate_password_hash(password)
                    if data is None:
                        cursor.execute("INSERT INTO User (FIRST_NAME, LAST_NAME, PASSWORD, ADDR_LN, CITY, STATE, WORKER_IND, EMAIL_ID) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (firstname, lastname, password, address, city, state, workerind, username))
                        db.commit()
                        return redirect(url_for('login'))
                    else:
                        error = 'User with that email alaready exists or you left it blank.. Please try again.'
                else:
                    error = 'Password must be atleast 6 characters and no more than 12 characters.'
            else:
                error = 'Email must be in the correct form: email@email.com'
        else:
            error = 'Cannot leave name fields blank'

    return render_template('signup.html', error=error)

if __name__ == "__main__":
    app.run()