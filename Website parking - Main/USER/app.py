from flask import Flask, render_template, session, request, g, redirect, url_for, send_file
import os
import sqlite3
import qrcode
import base64
from io import BytesIO
from pathlib import Path



#if you want to use the save info in the database the url must be http://localhost:5001/login

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL, platenumber TEXT NOT NULL)')
        db.commit()
    return db

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.before_request
def before_request():
    g.user = None

    if 'user' in session:
        g.user = session['user']

@app.route('/')
def index():
    return render_template('loading.html')

@app.route('/userview')
def userview():
    if g.user:
        return render_template('index.html', user=session['user'])
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()

        if user:
            session['user_id'] = user['id']
            session['user'] = user['username']
            if user:
                session.permanent = True
                session['user'] = user['username']
                return redirect(url_for('userview'))
        else:
            return render_template('login.html', error='Invalid username or password')

    # Handle GET requests
 #   if 'user_id' not in session:
  #      return redirect(url_for('login'))
   # return render_template('login.html')


    # Handle GET requests
    return render_template('login.html')

@app.route('/forgotpass')
def forgotpass():
    return render_template('forgotpass.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['name']
        platenumber = request.form['platenumber']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        db = get_db()

        try:
            db.execute('INSERT INTO users (username, platenumber, email, phone, password) VALUES (?, ?, ?, ?, ?)', (username, platenumber, email, phone, password))
            db.commit()
            session['user'] = username
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            return render_template('signup.html', error='Username already exists')

    return render_template('signup.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        platenumber = request.form['platenumber']
        db = get_db()
        db.execute('UPDATE users SET email = ?, phone = ?, platenumber = ? WHERE username = ?', (email, phone, platenumber, g.user))
        db.commit()
        return redirect(url_for('profile'))

    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE username = ?', [g.user])
    user = cur.fetchone()

    return render_template('profile.html', user=user)

@app.route('/qrcode',methods=['POST'])
def generate_qrcode():
    # Generate the data and the QR code image
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE username = ?', [g.user])
    user = cur.fetchone()
    data = f"Username: {user['username']}, Plate Number: {user['platenumber']}, Email: {user['email']}, Phone: {user['phone']}"
    img = qrcode.make(data)

    # Convert the image to a base64 encoded string
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    # Pass the base64 encoded string to the HTML template
    return render_template('qrcode.html', img_b64=img_b64)




@app.route('/download_qrcode', methods=['POST'])
def download_qrcode():
    downloads_dir = Path.home() / "Downloads"
    qrcode_path = downloads_dir / "qrcode.png"

    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE username = ?', [g.user])
    user = cur.fetchone()
    
    # Generate the QR code and save it to the downloads folder
    data = f"Username: {user['username']}, Plate Number: {user['platenumber']}, Email: {user['email']}, Phone: {user['phone']}"
    img = qrcode.make(data)
    img.save(qrcode_path)
    
    # Return a response to download the QR code image file
    return send_file(qrcode_path, as_attachment=True)



if __name__ == '__main__':
    app.run(port=5001)

    """"
@app.route('/download_qrcode', methods=['POST'])
def download_qrcode():
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE username = ?', [g.user])
    user = cur.fetchone()
    
    # Get the path to the user's downloads folder
    home_dir = os.path.expanduser("~")
    downloads_dir = os.path.join(home_dir, "Downloads")

    # Create the full path to the QR code image file
    qrcode_path = os.path.join(downloads_dir, "qrcode.png")
    
    # Generate the QR code and save it to the downloads folder
    data = f"Username: {user['username']}, Plate Number: {user['platenumber']}, Email: {user['email']}, Phone: {user['phone']}"
    img = qrcode.make(data)
    img.save(qrcode_path)

    # Return a response to download the QR code image file
    return send_file(qrcode_path, as_attachment=True)
"""

""""
@app.route('/download_qrcode', methods=['GET', 'POST'])
def download_qrcode():
    if request.method == 'POST':
        db = get_db()
        cur = db.execute('SELECT * FROM users WHERE username = ?', [g.user])
        user = cur.fetchone()
        data = f"Username: {user['username']}, Plate Number: {user['platenumber']}, Email: {user['email']}, Phone: {user['phone']}"
        img = qrcode.make(data)
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        path = os.path.join(os.path.expanduser("~"), "Downloads", "qrcode.png")
        img_io.save(path)
        return send_from_directory(directory=os.path.join(os.path.expanduser("~"), "Downloads"), filename="qrcode.png", as_attachment=True)
    else:
        return render_template('qrcode.html')
"""

""""
@app.route('/download_qrcode')
def download_qrcode():
    db= get_db()
    cur = db.execute('SELECT * FROM users WHERE username = ?', [g.user])
    user = cur.fetchone()
    data = f"Username: {user['username']}, Plate Number: {user['platenumber']}, Email: {user['email']}, Phone: {user['phone']}"
    img = qrcode.make(data)
    img.save('static/qrcode.png')
    return render_template('qrcode.html')

"""
#save qrcode as a file in static folder
""""
@app.route('/qrcode')
def generate_qrcode():
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE username = ?', [g.user])
    user = cur.fetchone()
    data = f"Username: {user['username']}, Plate Number: {user['platenumber']}, Email: {user['email']}, Phone: {user['phone']}"
    img = qrcode.make(data)
    img.save('static/qrcode.png')
    return render_template('qrcode.html')
"""