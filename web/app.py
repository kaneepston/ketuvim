import os
import sqlite3
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, g
from werkzeug.utils import secure_filename

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
DATABASE = os.path.join(os.path.dirname(__file__), 'ketuvim.db')

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database functions 
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_name TEXT UNIQUE,
            recognized_text TEXT,
            corrected_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def save_transcription_to_db(image_name, recognized_text, corrected_text):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''INSERT OR IGNORE INTO transcriptions (image_name, recognized_text, corrected_text) 
                      VALUES (?, ?, ?)''', (image_name, recognized_text, corrected_text))
    db.commit()

def update_transcription_in_db(image_name, corrected_text):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''UPDATE transcriptions SET corrected_text = ?, timestamp = ? WHERE image_name = ?''',
                   (corrected_text, datetime.now(), image_name))
    db.commit()

def get_all_transcriptions():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT image_name, recognized_text, corrected_text, timestamp FROM transcriptions')
    return cursor.fetchall()

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

# Placeholder for OCR processing 

def transcribe_image(image_path):
    return "This is the recognized text from the image."

# Flask Routes

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Check if the 'image' key is in request.files
        if 'image' not in request.files:
            return "No file part", 400
        file = request.files['image']
        if file.filename == '':
            return "No selected file", 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)
            # Call OCR processing
            raw_text = transcribe_image(image_path)
            # Save initial transcription (corrected_text is None at first)
            save_transcription_to_db(filename, raw_text, corrected_text=None)
            return render_template('edit.html', image_name=filename, recognized_text=raw_text)
    return render_template('upload.html')

@app.route('/save', methods=['POST'])
def save():
    image_name = request.form['image_name']
    corrected_text = request.form['corrected_text']
    update_transcription_in_db(image_name, corrected_text)
    return redirect(url_for('history'))

@app.route('/history', methods=['GET'])
def history():
    transcriptions = get_all_transcriptions()
    return render_template('history.html', transcriptions=transcriptions)

if __name__ == '__main__':
    init_db()  # Ensure database is initialized
    app.run(debug=True)
