'''
Inspiration: https://www.youtube.com/watch?v=pMIwu5FwJ78
'''

from flask import Flask, render_template, request, redirect, session

import numpy as np
import pymysql as pms
import random
import pickle
import secrets

import EncryptionLibrary

# REMEMBER to Modify this according to your setup
local_mysql_credentials = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YourPassword',
    'database': 'YourDatabase'
}

# USE this code to Create your own local credentials
# pickle.dump(local_mysql_credentials, open("local_mysql_credentials.pkl", 'wb'))
    
# Load MySQL Credentials
local_mysql_creds = pickle.load(open('local_mysql_credentials.pkl', 'rb'))
mysql_creds = local_mysql_creds
db = "mltlab" # Change according to preference

# Essentialy 'local_mysql_creds', is a pickled dictionary object,
# with 'host', 'user', 'password' and 'database' (optional)

# Test Connection
try:
    conn = pms.connect(host=mysql_creds['host'],
                       port=3306,
                       user=mysql_creds['user'],
                       password=mysql_creds['password'])

    cur = conn.cursor()
    cur.execute(f"DROP DATABASE {db};")
    
except Exception as e:
    print("Error connecting to database:", e)

# Create Relation (a.k.a. Table) to store the User Credentials
cur.execute(f"CREATE DATABASE {db};")
cur.execute(f"USE {db};")
cur.execute("CREATE TABLE credentials (email VARCHAR(70) PRIMARY KEY, username VARCHAR(50) UNIQUE NOT NULL, pwd VARCHAR(64) NOT NULL, salt INT);")
cur.execute("INSERT INTO credentials VALUES ('test1@gmail.com', 'test1', '323cf8a331de59dfcf2728bf2d2f83c79d6ba73c0046d195d454707b3aaf8b0c', 1);")

conn.commit()
conn.close()

#%%

app = Flask(__name__)
app.secret_key = secrets.token_hex(16) 


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template('index.html')

    if request.method == "POST":
        # Get Sign-in Credentials entered by the User
        email = request.form['email']
        password = request.form['password']
        
        # Check if email exists in the Database
        # If yes, check password. Else, prompt user to register.
        try:
            conn = pms.connect(host=mysql_creds['host'],
                               port=3306,
                               user=mysql_creds['user'],
                               password=mysql_creds['password'])
            
            cur = conn.cursor()
            cur.execute(f"USE {db};")
            cur.execute("SELECT email, pwd, salt FROM credentials;")
            res = cur.fetchall()
            conn.close()

        except Exception as e:
            print("Error connecting to database:", e)
            return render_template('index.html', error="Error connecting to database.")

        id_found = False
            
        for row in res:
            # Found the email in the Database
            if row[0] == email:
                id_found = True
                
                salt = row[2]
                password = EncryptionLibrary.Salted(password, salt)
                hashed_password = EncryptionLibrary.OneWayHashed(password)
            
                # Password Matches
                if hashed_password == row[1]:
                    session['email'] = email
                    return redirect('/predictor')
                # Password does not match
                else:
                    error_message = "Incorrect Password."
                    return render_template('index.html', error=error_message)

        if not id_found:
            error_message = "Email not registered."
            return render_template('index.html', error=error_message)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            error_message = "Passwords do not match."
            return render_template("signup.html", error=error_message)
        
        # Encrypt the Password before storing in Database
        salt = random.randint(0, 9)
        password = EncryptionLibrary.Salted(password, salt)
        hashed_password = EncryptionLibrary.OneWayHashed(password)
    
        try:
            conn = pms.connect(host=mysql_creds['host'],
                               port=3306,
                               user=mysql_creds['user'],
                               password=mysql_creds['password'])
            
            cur = conn.cursor()
            cur.execute(f"USE {db};")
            cur.execute("SELECT email, pwd, salt FROM credentials;")
            res = cur.fetchall()
            
            id_found = False
            for row in res:
                if row[0] == email:
                    id_found = True

            # If Email does NOT exist in Database,
            if not id_found:
                cur.execute(f"INSERT INTO credentials VALUES ('{email}', '{username}', '{hashed_password}', {salt});")
                conn.commit()
                conn.close()
                
                message = "Account registered successfully!"
                return render_template("signup.html", message=message)
            
            else:
                message = "Account already exists. Please Log-in."
                return render_template("signup.html", message=message)

        except Exception as e:
            print("Error connecting to database:", e)
            return render_template('signup.html', error="Error connecting to database.")


@app.route("/predictor", methods=["GET", "POST"])
def predictor():
    if 'email' not in session: # Check if user is logged in
        return redirect('/')

    pred_amt = None
    if request.method == "GET":
        return render_template("predictor.html")

    if request.method == "POST":
        # Data recieved is in 'string' datatype
        num_rooms = request.form['num_rooms']
        num_people = request.form['num_people']
        house_area = request.form['house_area']
        is_ac = request.form['is_ac']
        is_tv = request.form['is_tv']
        is_apartment = request.form['is_apartment']
        avg_monthly_income = request.form['avg_monthly_income']
        num_children = request.form['num_children']
        is_urban = request.form['is_urban']

        model = pickle.load(open('model.pkl', 'rb'))
        test_vector = [num_rooms, num_people, house_area, is_ac, is_tv, is_apartment, avg_monthly_income, num_children, is_urban]
        test_vector = np.array(test_vector).reshape(1, -1)
        test_vector = test_vector.astype(float)
        
        pred_val = model.predict(test_vector)
        pred_amt = round(pred_val[0], 2)
    
    return render_template("result.html", 
                           amount = pred_amt,
                           num_of_rooms = num_rooms,
                           num_of_people = num_people,
                           area = house_area,
                           ac = "Yes" if int(is_ac) == 1 else "No",
                           tv = "Yes" if int(is_tv) == 1 else "No",
                           apartment = "Yes" if int(is_apartment) == 1.0e+00 else "No",
                           monthly_income = avg_monthly_income,
                           num_of_children = num_children,
                           urban = "Yes" if int(is_urban) == 1 else "No",
                           )


if __name__ == "__main__":
    app.run(host='localhost', port=8361, debug=True)
    # You may enter any free port
