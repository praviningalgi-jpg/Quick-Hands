from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Register page (GET = show form, POST = save data)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Save to database
        conn = sqlite3.connect('requests.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                password TEXT
            )
        ''')
        cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                       (name, email, password))
        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    return render_template('register.html')

# Jobs page
@app.route('/jobs')
def jobs():
    return render_template('jobs.html')

# Contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)





