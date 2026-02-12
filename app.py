import os
import sqlite3
import csv
import io
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import (
    Flask, g, session, request, redirect, url_for,
    render_template, flash, jsonify, make_response
)

# ------------------------------------------------------------
# APP CONFIGURATION
# ------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'supersecretkey4studentresultapp'  # change in production

# Upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------------------------------------------------
# DATABASE HELPERS
# ------------------------------------------------------------
DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Create tables if they don't exist."""
    db = get_db()
    cursor = db.cursor()

    # users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            board TEXT,
            exam TEXT,
            school TEXT,
            class_name TEXT,
            year INTEGER,
            total_obtained INTEGER,
            total_marks INTEGER,
            percentage REAL,
            grade TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL,
            subject_name TEXT NOT NULL,
            obtained INTEGER NOT NULL,
            total INTEGER NOT NULL,
            FOREIGN KEY (result_id) REFERENCES results (id) ON DELETE CASCADE
        )
    ''')
    db.commit()

# ------------------------------------------------------------
# LOGIN REQUIRED DECORATOR
# ------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------------
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_grade(percentage):
    if percentage >= 90: return 'A+'
    elif percentage >= 80: return 'A'
    elif percentage >= 70: return 'B'
    elif percentage >= 60: return 'C'
    elif percentage >= 50: return 'D'
    else: return 'F'

# ------------------------------------------------------------
# ROUTES: AUTHENTICATION
# ------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # validation
        if not all([name, email, password, confirm]):
            flash('All fields are required.', 'danger')
            return render_template('auth.html', active='register')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth.html', active='register')

        db = get_db()
        existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('Email already registered. Please login.', 'danger')
            return render_template('auth.html', active='register')

        password_hash = generate_password_hash(password)
        db.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                   (name, email, password_hash))
        db.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('auth.html', active='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('auth.html', active='login')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return render_template('auth.html', active='login')

    return render_template('auth.html', active='login')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ------------------------------------------------------------
# ROUTES: DASHBOARD & RESULTS
# ------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    search = request.args.get('search', '').strip()
    sort = request.args.get('sort', 'desc')  # default highest percentage first

    db = get_db()
    query = 'SELECT * FROM results WHERE user_id = ?'
    params = [user_id]

    if search:
        query += ' AND student_name LIKE ?'
        params.append(f'%{search}%')

    if sort == 'desc':
        query += ' ORDER BY percentage DESC'
    else:
        query += ' ORDER BY percentage ASC'

    results = db.execute(query, params).fetchall()

    # statistics
    total_results = len(results)
    if total_results > 0:
        avg_percentage = sum(r['percentage'] for r in results) / total_results
        highest_percentage = max(r['percentage'] for r in results)
    else:
        avg_percentage = 0
        highest_percentage = 0

    return render_template('dashboard.html',
                           results=results,
                           total_results=total_results,
                           avg_percentage=round(avg_percentage, 2),
                           highest_percentage=round(highest_percentage, 2),
                           search=search, sort=sort)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_result():
    if request.method == 'POST':
        user_id = session['user_id']
        student_name = request.form.get('student_name')
        board = request.form.get('board')
        exam = request.form.get('exam')
        school = request.form.get('school')
        class_name = request.form.get('class_name')
        year = request.form.get('year')

        # dynamic subject handling
        subject_names = request.form.getlist('subject_name[]')
        obtained_marks = request.form.getlist('obtained[]')
        total_marks_list = request.form.getlist('total[]')

        # validation
        if not student_name:
            flash('Student name is required.', 'danger')
            return redirect(url_for('add_result'))

        # compute totals
        total_obtained = 0
        total_marks = 0
        subjects = []
        for name, obt, tot in zip(subject_names, obtained_marks, total_marks_list):
            if name.strip() and obt.strip() and tot.strip():
                obt_int = int(obt)
                tot_int = int(tot)
                subjects.append((name.strip(), obt_int, tot_int))
                total_obtained += obt_int
                total_marks += tot_int

        if total_marks == 0:
            flash('Total marks cannot be zero.', 'danger')
            return redirect(url_for('add_result'))

        percentage = (total_obtained / total_marks) * 100
        grade = calculate_grade(percentage)

        # image upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f'uploads/{filename}'

        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO results
            (user_id, student_name, board, exam, school, class_name, year,
             total_obtained, total_marks, percentage, grade, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, student_name, board, exam, school, class_name, year,
              total_obtained, total_marks, percentage, grade, image_path))
        result_id = cursor.lastrowid

        # insert subjects
        for sub_name, obt, tot in subjects:
            cursor.execute('''
                INSERT INTO subjects (result_id, subject_name, obtained, total)
                VALUES (?, ?, ?, ?)
            ''', (result_id, sub_name, obt, tot))
        db.commit()

        flash('Result added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_edit_result.html', result=None)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_result(id):
    user_id = session['user_id']
    db = get_db()
    result = db.execute('SELECT * FROM results WHERE id = ? AND user_id = ?',
                        (id, user_id)).fetchone()
    if not result:
        flash('Result not found or access denied.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        student_name = request.form.get('student_name')
        board = request.form.get('board')
        exam = request.form.get('exam')
        school = request.form.get('school')
        class_name = request.form.get('class_name')
        year = request.form.get('year')

        subject_names = request.form.getlist('subject_name[]')
        obtained_marks = request.form.getlist('obtained[]')
        total_marks_list = request.form.getlist('total[]')

        if not student_name:
            flash('Student name is required.', 'danger')
            return redirect(url_for('edit_result', id=id))

        total_obtained = 0
        total_marks = 0
        subjects = []
        for name, obt, tot in zip(subject_names, obtained_marks, total_marks_list):
            if name.strip() and obt.strip() and tot.strip():
                obt_int = int(obt)
                tot_int = int(tot)
                subjects.append((name.strip(), obt_int, tot_int))
                total_obtained += obt_int
                total_marks += tot_int

        if total_marks == 0:
            flash('Total marks cannot be zero.', 'danger')
            return redirect(url_for('edit_result', id=id))

        percentage = (total_obtained / total_marks) * 100
        grade = calculate_grade(percentage)

        # image handling
        image_path = result['image_path']
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # delete old image if exists
                if image_path:
                    old_path = os.path.join('static', image_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f'uploads/{filename}'

        # update result
        db.execute('''
            UPDATE results SET
                student_name=?, board=?, exam=?, school=?, class_name=?, year=?,
                total_obtained=?, total_marks=?, percentage=?, grade=?, image_path=?
            WHERE id=? AND user_id=?
        ''', (student_name, board, exam, school, class_name, year,
              total_obtained, total_marks, percentage, grade, image_path,
              id, user_id))
        db.commit()

        # delete old subjects and insert new ones
        db.execute('DELETE FROM subjects WHERE result_id = ?', (id,))
        for sub_name, obt, tot in subjects:
            db.execute('''
                INSERT INTO subjects (result_id, subject_name, obtained, total)
                VALUES (?, ?, ?, ?)
            ''', (id, sub_name, obt, tot))
        db.commit()

        flash('Result updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # GET: load subjects for this result
    subjects = db.execute('SELECT * FROM subjects WHERE result_id = ?', (id,)).fetchall()
    return render_template('add_edit_result.html', result=result, subjects=subjects)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_result(id):
    user_id = session['user_id']
    db = get_db()
    result = db.execute('SELECT image_path FROM results WHERE id = ? AND user_id = ?',
                        (id, user_id)).fetchone()
    if result:
        # delete image file if exists
        if result['image_path']:
            file_path = os.path.join('static', result['image_path'])
            if os.path.exists(file_path):
                os.remove(file_path)
        # delete result (cascades to subjects)
        db.execute('DELETE FROM results WHERE id = ? AND user_id = ?', (id, user_id))
        db.commit()
        flash('Result deleted successfully.', 'success')
    else:
        flash('Result not found or access denied.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/view/<int:id>')
@login_required
def view_result(id):
    user_id = session['user_id']
    db = get_db()
    result = db.execute('SELECT * FROM results WHERE id = ? AND user_id = ?',
                        (id, user_id)).fetchone()
    if not result:
        flash('Result not found or access denied.', 'danger')
        return redirect(url_for('dashboard'))
    subjects = db.execute('SELECT * FROM subjects WHERE result_id = ?', (id,)).fetchall()
    return render_template('view_result.html', result=result, subjects=subjects)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_new = request.form.get('confirm_new_password', '')

        # verify current password
        if not check_password_hash(user['password_hash'], current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('profile'))

        # update name and email
        if name and email:
            # check email uniqueness if changed
            if email != user['email']:
                existing = db.execute('SELECT id FROM users WHERE email = ? AND id != ?',
                                      (email, user_id)).fetchone()
                if existing:
                    flash('Email already in use.', 'danger')
                    return redirect(url_for('profile'))
            # update
            db.execute('UPDATE users SET name = ?, email = ? WHERE id = ?',
                       (name, email, user_id))
            session['user_name'] = name
            session['user_email'] = email
            flash('Profile updated successfully.', 'success')

        # change password if provided
        if new_password:
            if new_password != confirm_new:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('profile'))
            password_hash = generate_password_hash(new_password)
            db.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                       (password_hash, user_id))
            flash('Password changed successfully.', 'success')

        db.commit()
        return redirect(url_for('profile'))

    # total results count for profile
    total_results = db.execute('SELECT COUNT(*) as cnt FROM results WHERE user_id = ?',
                               (user_id,)).fetchone()['cnt']
    return render_template('profile.html', user=user, total_results=total_results)

@app.route('/export/csv')
@login_required
def export_csv():
    user_id = session['user_id']
    db = get_db()
    results = db.execute('''
        SELECT * FROM results WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    # create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Student Name', 'Board', 'Exam', 'School', 'Class',
        'Year', 'Total Obtained', 'Total Marks', 'Percentage', 'Grade',
        'Image Path', 'Created At'
    ])

    for r in results:
        writer.writerow([
            r['id'], r['student_name'], r['board'], r['exam'], r['school'],
            r['class_name'], r['year'], r['total_obtained'], r['total_marks'],
            f"{r['percentage']:.2f}", r['grade'], r['image_path'], r['created_at']
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=my_results.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

# ------------------------------------------------------------
# INITIALIZE DATABASE ON FIRST RUN
# ------------------------------------------------------------
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)