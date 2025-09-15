from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # needed for login sessions

# ---------- DATABASE HELPER ----------
def get_db_connection():
    conn = sqlite3.connect("requests.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- CREATE APPLICATIONS TABLE ----------
def create_applications_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            maid_id INTEGER,
            cover_letter TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY(job_id) REFERENCES jobs(id),
            FOREIGN KEY(maid_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

create_applications_table()

# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']  # maid or household

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("Email already registered. Please login or use a different email.")
            return redirect(url_for('register'))

        cursor.execute(
            'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
            (name, email, password, role)
        )
        conn.commit()
        conn.close()

        flash("Registered successfully! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            flash(f"Welcome, {user['name']}!")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password. Please try again.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('home'))

# Jobs list
@app.route('/jobs')
def jobs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT jobs.*, users.name as posted_by_name
        FROM jobs JOIN users ON jobs.posted_by = users.id
    """)
    jobs = cursor.fetchall()
    conn.close()
    return render_template('jobs.html', jobs=jobs)

# Post job
@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if not session.get('user_id') or session.get('role') != 'household':
        flash("Please log in as a household user to post jobs.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        location = request.form['location']
        salary = request.form['salary']
        description = request.form['description']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (title, location, salary, description, posted_by)
            VALUES (?, ?, ?, ?, ?)
        """, (title, location, salary, description, session['user_id']))
        conn.commit()
        conn.close()

        flash("Job posted successfully!")
        return redirect(url_for('jobs'))

    return render_template('post_job.html')

# Apply for job
@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply(job_id):
    if not session.get('user_id') or session.get('role') != 'maid':
        flash("Please log in as a maid to apply.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        cover_letter = request.form['cover_letter']
        cursor.execute("""
            INSERT INTO applications (job_id, maid_id, cover_letter)
            VALUES (?, ?, ?)
        """, (job_id, session['user_id'], cover_letter))
        conn.commit()
        conn.close()

        flash("Application submitted successfully!")
        return redirect(url_for('jobs'))

    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    conn.close()

    if job is None:
        flash("Job not found.")
        return redirect(url_for('jobs'))

    return render_template('apply_job.html', job=job)

# View applications for household users
@app.route('/view_applications')
def view_applications():
    if not session.get('user_id') or session.get('role') != 'household':
        flash("Please log in as a household user to view applications.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT applications.*, jobs.title, users.name as maid_name
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN users ON applications.maid_id = users.id
        WHERE jobs.posted_by = ?
        ORDER BY applications.id DESC
    """, (session['user_id'],))
    applications = cursor.fetchall()
    conn.close()
    return render_template('view_applications.html', applications=applications)

# Approve application
@app.route('/application/<int:app_id>/approve')
def approve_application(app_id):
    if not session.get('user_id') or session.get('role') != 'household':
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT applications.id FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.id = ? AND jobs.posted_by = ?
    """, (app_id, session['user_id']))
    app_record = cursor.fetchone()

    if app_record:
        cursor.execute("UPDATE applications SET status = ? WHERE id = ?", ('approved', app_id))
        conn.commit()
        flash("Application approved.")
    else:
        flash("Application not found or unauthorized.")

    conn.close()
    return redirect(url_for('view_applications'))

# Reject application
@app.route('/application/<int:app_id>/reject')
def reject_application(app_id):
    if not session.get('user_id') or session.get('role') != 'household':
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT applications.id FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.id = ? AND jobs.posted_by = ?
    """, (app_id, session['user_id']))
    app_record = cursor.fetchone()

    if app_record:
        cursor.execute("UPDATE applications SET status = ? WHERE id = ?", ('rejected', app_id))
        conn.commit()
        flash("Application rejected.")
    else:
        flash("Application not found or unauthorized.")

    conn.close()
    return redirect(url_for('view_applications'))

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)









