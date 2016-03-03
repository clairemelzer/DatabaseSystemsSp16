from flask import Flask
from flask_mysqldb import MySQL
from flaskext.mysql import MySQL
from flask import Flask, render_template, redirect, url_for, request


mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'gocubs_1'
app.config['MYSQL_DATABASE_DB'] = 'Project'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

@app.route("/")
def home():
    return "Welcome to the Disaster Help Site!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connect().cursor()
        cursor.execute("SELECT * from User where Username='" + username + "' and Password='" + password + "'")
        data = cursor.fetchone()
        if data is None:
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect(url_for('home'))
    return render_template('login.html', error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        address = request.form['address']
        password = request.form['password']
        validation = request.form['workercode']
        db = mysql.connect()
        cursor = db.cursor()
        cursor.execute("INSERT INTO User (idUser, Username, Password) VALUES ('%d', '%s', '%s')" % (2, username, password))
        db.commit()
        
        return redirect(url_for('login'))
    return render_template('signup.html', error=error)

if __name__ == "__main__":
    app.run()