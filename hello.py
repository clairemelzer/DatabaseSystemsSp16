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

            #STORED PROCEDURES

            args = [id, 0]
            result_args = cursor.callproc('find_admin', args)
            admin = result_args[0]

            args = [id, 0]
            result_args = cursor.callproc('find_worker_ind', args)
            worker = result_args[0]

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
                        if validation == "123193":
                            cursor.execute("INSERT INTO Worker (USER_ID) SELECT USER_ID from User where EMAIL_ID = '%s'" % (username))
                        db.commit()
                        flash('Signed Up successfully!')
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
    result = None
    db = mysql.connect()
    cursor = db.cursor()
    cursor.execute("SELECT DISASTER_NAME, ITEM_NAME, ITEM_QUANTITY, REQUESTOR_EMAILID from Request")
    result = cursor.fetchall()

    return render_template('requests.html', result=result)

@app.route('/responses')
def responses():
    result = None
    db = mysql.connect()
    cursor = db.cursor()
    cursor.execute("SELECT DISASTER_NAME, ITEM_NAME, ITEM_QUANTITY, RESPONDER_ID from Request WHERE RESPONSE_ID IS NOT NULL")
    result = cursor.fetchall()

    return render_template('responses.html', result = result)

@app.route('/disasters')
def disasters():
    result = None
    db = mysql.connect()
    cursor = db.cursor()
    cursor.execute("SELECT EVENT_NAME, ZIP_CODE, EVENT_DATE from EVENT")
    result = cursor.fetchall()
    return render_template('disasters.html', result=result)

@app.route('/centers')
def centers():
    result = None
    db = mysql.connect()
    cursor = db.cursor()
    cursor.execute("SELECT RELIEF_CNTR_NAME, ZIP_CODE from RELIEF_CENTER")
    result = cursor.fetchall()
    return render_template('centers.html', result=result)

@app.route('/create_center', methods=['GET', 'POST'])
def create_center():
    error = None
    if request.method == 'POST':
        centername = request.form['centername']
        centerzipcode = request.form['centerzipcode']

        db = mysql.connect()
        cursor = db.cursor()
        
        if len(centername) > 0:
            if re.match(r'(\d{5})', centerzipcode):
                centerzipcode = int(centerzipcode)
                cursor.execute("INSERT INTO RELIEF_CENTER (RELIEF_CNTR_NAME, ZIP_CODE) VALUES ('%s', '%d')" % (centername, centerzipcode))
                db.commit()
                flash('Created Center successfully!')
                return redirect(url_for('home'))
            else:
                error = "Zipcode not in the right format. Date Format: YYYY-MM-DD"
        else:
            error = "Must enter a center name"
    
    return render_template('create_center.html', error=error)

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
                cursor.execute("INSERT INTO EVENT (EVENT_NAME, ZIP_CODE, EVENT_DATE, CATEGORIES) VALUES ('%s', '%d', '%s', '%s')" % (eventname, eventzipcode, eventdate, categories))
                db.commit()
                flash('Created Disaster successfully!')
                return redirect(url_for('home'))
            else:
                error = "Date or zipcode not in the right format. Date Format: YYYY-MM-DD"
        else:
            error = "Must enter an event name"

    return render_template('create_disaster.html', error=error)

@app.route('/gethelp', methods=['GET', 'POST'])
def gethelp():
    error = None
    result = None
    center = None
    db = mysql.connect()
    cursor = db.cursor()

    cursor.execute("SELECT RELIEF_CNTR_NAME from RELIEF_CENTER")
    center = cursor.fetchall()
    cursor.execute("SELECT EVENT_NAME from EVENT")
    result = cursor.fetchall()
    
    render_template('gethelp.html', error=error, center=center, result = result)

    if request.method == 'POST':
        itemname = request.form['itemname']
        quantity= request.form['quantity']
        expiration = request.form['expirationdate']
        zipcode = request.form['zipcode']
        disaster = request.form.get('disaster')
        category = request.form.get('category')
        center = request.form.get('center')
        
        id = current_user.id[0]
        id = int(id)

        cursor.execute("SELECT EMAIL_ID from USER where USER_ID = '%d'" % (id))
        email = cursor.fetchone()
        email = email[0]

        cursor.execute("SELECT RELIEF_CNTR_ID from RELIEF_CENTER where RELIEF_CNTR_NAME = '%s'" % (center))
        rc_id = cursor.fetchone()
        rc_id = rc_id[0]
        
        cursor.execute("SELECT * from Request where ITEM_NAME= '%s' AND DISASTER_NAME = '%s'" % (itemname, disaster))
        data = cursor.fetchone()
    
    
        if data == None:
        
            if len(itemname) > 0:
                if re.match(r'(\d{4}-\d{2}-\d{2})', expiration) and re.match(r'(\d+)', quantity) and re.match(r'(\d{5})', zipcode):
                    zipcode = int(zipcode)
                    quantity = int(quantity)
                    cursor.execute("INSERT INTO Request (ITEM_NAME, ZIP_CODE, EXPIRATION_DATE, ITEM_QUANTITY, DISASTER_NAME, CATEGORY_NAME, CREATED_DATE, REQUESTOR_EMAILID, RELIEF_CNTR_ID) VALUES ('%s', '%d', '%s', '%d', '%s', '%s', CURRENT_DATE, '%s', '%d' )" % (itemname, zipcode, expiration, quantity, disaster, category, email, rc_id))
                    db.commit()
                    flash('Request Submitted!')
                    return redirect(url_for('home'))
                else:
                    error = "Date or quantity not in the right format. Date Format: YYYY-MM-DD. Quantity must be a number. Zipcode must be 5 digits"
            else:
                error = "Must enter an item name"
        else:
            
            cursor.execute("SELECT ITEM_QUANTITY from Request where ITEM_NAME = '%s'" % (itemname))
            item_quantity = cursor.fetchone()[0]
            item_quantity = int(item_quantity)
            quantity = int(quantity)
            sum = quantity + item_quantity
     
            cursor.execute("SET SQL_SAFE_UPDATES=0")
            cursor.execute("UPDATE Request set ITEM_QUANTITY = '%d' WHERE ITEM_NAME = '%s' AND DISASTER_NAME = '%s'" % (sum, itemname, disaster))
            db.commit()
            flash('Requested item already exists, added your quantity to the quantity already requested!')
            return redirect(url_for('home'))
    
    return render_template('gethelp.html', error=error, result = result, center = center)

@app.route('/givehelp', methods=['GET', 'POST'])
def givehelp():
    search = ""
    result = None
    if request.method == 'POST':
        zipcode = request.form['searchzip']
        

        db = mysql.connect()
        cursor = db.cursor()
        zipcode = int(zipcode)
        
        cursor.execute("SELECT DISASTER_NAME, ITEM_NAME, ITEM_QUANTITY, ZIP_CODE from Request WHERE ZIP_CODE = '%d'" % (zipcode))
        result = cursor.fetchall()
        search = "done"

    return render_template('givehelp.html', result = result, search = search)

@app.route('/respond/<requestid>', methods=['GET', 'POST'])
def response(requestid):
    error = None
    db = mysql.connect()
    cursor = db.cursor()
    requestid = int(requestid)
    cursor.execute("SELECT ITEM_NAME from Request WHERE REQUEST_ID = '%d'" % (requestid))
    request_item = cursor.fetchall()
    request_item = request_item[0]
    
    cursor.execute("SELECT DISASTER_NAME from Request WHERE REQUEST_ID = '%d'" % (requestid))
    disaster = cursor.fetchall()
    disaster = disaster[0]
    
    cursor.execute("SELECT ITEM_QUANTITY from Request WHERE REQUEST_ID = '%d'" % (requestid))
    it_quant = cursor.fetchall()
    it_quant = it_quant[0]
    
    
    if request.method == 'POST':
        quantity = request.form['quantity']
        quantity = int(quantity)
        it_quant = int(it_quant[0])
        if quantity <= it_quant:
            
            id = current_user.id[0]
            id = int(id)
            
            updated_quant = it_quant - quantity
            cursor.execute("SET SQL_SAFE_UPDATES=0")
            cursor.execute("UPDATE Request set ITEM_QUANTITY = '%d' WHERE REQUEST_ID = '%d'" % (updated_quant, requestid))
            db.commit()
          
            cursor.execute("INSERT INTO Response (ITEM_NAME, DISASTER_NAME, ITEM_QUANTITY, REQUEST_ID, RESP_USER_ID, RESP_CREATED_DT) VALUES ('%s', '%s', '%d', '%d', '%d', CURRENT_DATE)" % (request_item[0], disaster[0], quantity, requestid, id))
            db.commit()
            flash('Your Response was Recieved!')
            return redirect(url_for('home'))
    
    
    
    return render_template('respond.html', request_item = request_item, error = error, disaster = disaster, it_quant = it_quant)


if __name__ == "__main__":
    app.run()