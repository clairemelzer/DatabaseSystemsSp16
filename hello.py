from flask import Flask
from flask.ext.login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask.ext.bcrypt import Bcrypt
from flask_mysqldb import MySQL
from flaskext.mysql import MySQL
from flask import Flask, render_template, redirect, url_for, request, flash
import re
from werkzeug.security import generate_password_hash, check_password_hash


mysql = MySQL()
app = Flask(__name__)
login_manager = LoginManager()
app.debug = True
app.secret_key = 'some_secret'
bcrypt = Bcrypt(app)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'gocubs_1'
app.config['MYSQL_DATABASE_DB'] = 'DMS'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, username, id, worker, admin):
        self.username = username
        self.id = id
        self.admin = admin
        self.worker = worker
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id

    def is_worker(self):
        if self.worker == "Y":
            return True
        else:
            return False

    def is_admin(self):
        if self.admin == "Y":
            return True
        else:
            return False



@login_manager.user_loader
def load_user(id):
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT EMAIL_ID from User where USER_ID= %d" % id)
    username = cursor.fetchone()[0]
    cursor.execute("SELECT ADMIN_IND from User where USER_ID= %d" % id)
    admin = cursor.fetchone()[0]
    cursor.execute("SELECT WORKER_IND from User where USER_ID= %d" % id)
    worker = cursor.fetchone()[0]
    return User(username, id, worker, admin)



@app.route("/")

def home():
    return render_template('index.html')

#login_manager.login_view = "users.login"

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
            cursor.execute("SELECT USER_ID from User where EMAIL_ID='" + username + "'")
            id = cursor.fetchone()
            cursor.execute("SELECT ADMIN_IND from User where USER_ID= %d" % id)
            admin = cursor.fetchone()
            cursor.execute("SELECT WORKER_IND from User where USER_ID= %d" % id)
            worker = cursor.fetchone()
            user = User(username, id, worker, admin)
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('home'))
        else:
            error = 'Invalid Credentials. Please try again.'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out')
    return redirect(url_for('home'))

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
                        #if validation == "123193":
                            #cursor.execute("INSERT INTO Worker (USER_ID) VALUES (SELECT USER_ID from User where EMAIL_ID = '%s')" % (username))
                        #end if
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


@app.route('/requests')
def requests():
    db = mysql.connect()
    cursor = db.cursor()
    #cursor.execute("SELECT DISASTER_NAME, ITEM_NAME, QUANTITY from Request")
    result = cursor.fetchall()

    return render_template('requests.html', result=result)

@app.route('/responses')
def responses():
    return render_template('responses.html')

@app.route('/disasters')
def disasters():
    db = mysql.connect()
    cursor = db.cursor()
    #cursor.execute("SELECT EVENT_NAME, EVENT_ZIPCODE from EVENT")
    result = cursor.fetchall()
    return render_template('disasters.html', result=result)


@app.route('/create_disaster', methods=['GET', 'POST'])
def create_disaster():
    error = None
    if request.method == 'POST':
        eventname = request.form['eventname']
        eventdate = request.form['eventdate']
        eventzipcode = request.form['eventzipcode']
        food = request.form.getlist('food')
        clothing = request.form.getlist('clothing')
        shelter = request.form.getlist('shelter')
        medicine = request.form.getlist('medicine')
        volunteers = request.form.getlist('volunteers')
        transportation = request.form.getlist('transportation')
        consumables = request.form.getlist('consumables')
        
        
        categories = ""
        if food:
            food = food[0]
            categories = food
        if clothing:
            clothing = clothing[0]
            categories = categories + "," + clothing
        if shelter:
            shelter = shelter[0]
            categories = categories + "," + shelter
        if medicine:
            medicine = medicine[0]
            categories = categories + "," + medicine
        if volunteers:
            volunteers = volunteers[0]
            categories = categories + "," + volunteers
        if transportation:
            transportation = transportation[0]
            categories = categories + "," + transportation
        if consumables:
            consumables = consumables[0]
            categories = categories + "," + consumables

    
        db = mysql.connect()
        cursor = db.cursor()

        if len(eventname) > 0:
            if re.match(r'(\d{4}-\d{2}-\d{2})', eventdate) and re.match(r'(\d{5})', eventzipcode):
                eventzipcode = int(eventzipcode)
                flash(categories)
            #                cursor.execute("INSERT INTO EVENT (EVENT_NAME, EVENT_ZIPCODE, EVENT_DATE, CATEGORIES) VALUES ('%s', '%d', '%s', '%s')" % (eventname, eventzipcode, eventdate, categories))
            #db.commit()
                return redirect(url_for('home'))
            else:
                error = "Date or zipcode not in the right format. Date Format: YYYY-MM-DD"
        else:
            error = "Must enter an event name"

    return render_template('create_disaster.html', error=error)

@app.route('/gethelp', methods=['GET', 'POST'])
def gethelp():
    error = None
    db = mysql.connect()
    cursor = db.cursor()
    #UPDATE
    cursor.execute("SELECT FIRST_NAME from User")
    result = cursor.fetchall()
    render_template('gethelp.html', error=error, result = result)

    if request.method == 'POST':
        itemname = request.form['itemname']
        quantity= request.form['quantity']
        expiration = request.form['expirationdate']
        zipcode = request.form['zipcode']
        disaster = request.form.get('disaster')
        category = request.form.get('category')
        
        id = current_user.get_id


        if len(itemname) > 0:
            if re.match(r'(\d{4}-\d{2}-\d{2})', expiration) and re.match(r'(\d+)', quantity) and re.match(r'(\d{5})', zipcode):
                zipcode = int(zipcode)
                quantity = int(quantity)
                #cursor.execute("INSERT INTO Requests (Item_NAME, ZIPCODE, Expiration_DATE, Quantity, Disaster, category, created_date, requester_id) VALUES ('%s', '%d', '%s', '%d', '%s', '%s', CURRENT_DATE, '%d' )" % (itemname, zipcode, expiration, quantity, disaster, category, id))
                #db.commit()
                flash(disaster)
                return redirect(url_for('home'))
            else:
                error = "Date or quantity not in the right format. Date Format: YYYY-MM-DD. Quantity must be a number. Zipcode must be 5 digits"
        else:
            error = "Must enter an item name"
    return render_template('gethelp.html', error=error, result = result)

@app.route('/givehelp', methods=['GET', 'POST'])
def givehelp():
    search = ""
    result = None
    if request.method == 'POST':
        zipcode = request.form['searchzip']
        search = "done"

        return render_template('givehelp.html', search=search)
    
    if search == "done":
        db = mysql.connect()
        cursor = db.cursor()

        #cursor.execute("SELECT EVENT_NAME, ITEM_NAME, QUANTITY, EVENT_ZIPCODE from Requests WHERE EVENT_ZIPCODE = '%s'") % (zipcode)

        #result = cursor.fetchall()
    return render_template('givehelp.html', result = result)

if __name__ == "__main__":
    app.run()