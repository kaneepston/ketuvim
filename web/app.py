import os
import sqlite3
from datetime import datetime
from flask import (
    Flask, request, render_template, redirect, url_for, g, send_from_directory, flash, jsonify
)
from werkzeug.utils import secure_filename
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# --- Configuration ---
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
DATABASE = os.path.join(BASE_DIR, 'ketuvim.db')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
NERT_MODEL_PATH = os.path.join(MODEL_DIR, 'ketuvim_nert')

# --- Initialize Flask app ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_ABSOLUTE'] = os.path.abspath(UPLOAD_FOLDER)
os.makedirs(app.config['UPLOAD_FOLDER_ABSOLUTE'], exist_ok=True)

# --- Load Models ---
def load_nert_model(path):
    if not os.path.isdir(path):
        print(f"ERROR: NERT model directory not found at {path}")
        return None, None
    try:
        tokenizer = AutoTokenizer.from_pretrained(path)
        model = AutoModelForSeq2SeqLM.from_pretrained(path)
        print(f"NERT model loaded successfully from {path}.")
        return tokenizer, model
    except ImportError:
        print("ERROR: transformers or torch library not found. Please install.")
        return None, None
    except Exception as e:
        print(f"ERROR loading NERT model/tokenizer: {e}")
        return None, None

nert_tokenizer, nert_model = load_nert_model(NERT_MODEL_PATH)
if not (nert_tokenizer and nert_model):
    print("WARNING: NERT model failed to load. Correction functionality will be disabled.")

# --- Database Setup ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    try:
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_name TEXT UNIQUE NOT NULL,
            input_text TEXT,
            corrected_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        db.commit()
        db.close()
        print("Database initialized.")
    except sqlite3.Error as e:
        print(f"ERROR initializing database: {e}")

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Database Operations ---
def save_or_update_transcription(image_name, input_text, corrected_text):
    sql = '''INSERT OR REPLACE INTO transcriptions (image_name, input_text, corrected_text, timestamp)
             VALUES (?, ?, ?, ?)'''
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(sql, (image_name, input_text, corrected_text, datetime.now()))
        db.commit()
    except sqlite3.Error as e:
        print(f"ERROR saving transcription for {image_name}: {e}")
        flash(f"Database error saving transcription for {image_name}.", "error")

def get_transcription_data(image_name=None):
    try:
        db = get_db()
        cursor = db.cursor()
        if image_name:
            cursor.execute('SELECT image_name, input_text, corrected_text, timestamp FROM transcriptions WHERE image_name = ?', (image_name,))
            return cursor.fetchone()
        else:
            cursor.execute('SELECT image_name, input_text, corrected_text, timestamp FROM transcriptions ORDER BY timestamp DESC')
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"ERROR fetching transcription data: {e}")
        flash("Database error fetching transcription data.", "error")
        return None if image_name else []

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

# --- NERT Processing Function ---
def run_nert_corrector(text, tokenizer, model):
    if not text or not tokenizer or not model:
        return text if text else ""
    try:
        input_text_with_prefix = "correct: " + text
        inputs = tokenizer(input_text_with_prefix, return_tensors="pt", truncation=True, max_length=512)

        # device = model.device
        # inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
             outputs = model.generate(
                 inputs['input_ids'],
                 max_length=512,
                 num_beams=4,
                 early_stopping=True
             )
        corrected_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return corrected_text
    except Exception as e:
        print(f"ERROR during NERT correction: {e}")
        return text # Return original text on error

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('main.html', page_title="Process Image and Text")

# *** RENAMED FUNCTION HERE ***
@app.route('/process', methods=['POST'])
def process(): # Renamed from process_submission
    if not (nert_tokenizer and nert_model):
        flash("NERT model is not loaded, cannot process text.", "error")
        return redirect(url_for('index'))

    if 'image' not in request.files:
        flash('No image file part selected.', 'error')
        return redirect(url_for('index'))

    file = request.files['image']
    input_text = request.form.get('input_text', '').strip()

    if file.filename == '':
        flash('No image selected for uploading.', 'error')
        return redirect(url_for('index'))

    if not input_text:
        flash('No input text provided.', 'error')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        try:
            image_path = os.path.join(app.config['UPLOAD_FOLDER_ABSOLUTE'], filename)
            file.save(image_path)

            corrected_text = run_nert_corrector(input_text, nert_tokenizer, nert_model)
            save_or_update_transcription(filename, input_text, corrected_text)

            # Redirect using the correct function name for the edit page route
            return redirect(url_for('edit_page', filename=filename))

        except Exception as e:
            print(f"ERROR during file saving or NERT processing: {e}")
            flash(f"An error occurred during processing: {e}", "error")
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Allowed types: png, jpg, jpeg.', 'error')
        return redirect(url_for('index'))

@app.route('/edit/<filename>')
def edit_page(filename):
    entry = get_transcription_data(image_name=filename)
    if not entry:
        flash(f"No record found for image: {filename}", "error")
        return redirect(url_for('index'))

    return render_template('edit.html',
                           image_name=entry['image_name'],
                           input_text=entry['input_text'],
                           corrected_text=entry['corrected_text'],
                           page_title=f"ketuvim_nert for {entry['image_name']}")

@app.route('/save', methods=['POST'])
def save_edited():
    image_name = request.form.get('image_name')
    final_corrected_text = request.form.get('corrected_text', '')
    input_text = request.form.get('input_text', '')

    if not image_name:
         # Return error JSON for JavaScript fetch
         return jsonify(success=False, message="Missing image name for saving."), 400

    try:
        save_or_update_transcription(image_name, input_text, final_corrected_text)
        # Return success JSON
        return jsonify(success=True)
    except Exception as e:
        print(f"ERROR saving final corrected text: {e}")
        # Return error JSON
        return jsonify(success=False, message=f"An error occurred while saving: {e}"), 500

@app.route('/history')
def history():
    transcriptions = get_transcription_data()
    return render_template('history.html',
                            transcriptions=transcriptions,
                            page_title="Transcription History")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER_ABSOLUTE'], filename)
    except FileNotFoundError:
        return "File not found", 404

# --- Main Execution Block ---
if __name__ == '__main__':
    print("Initializing database...")
    init_db()

    if not (nert_tokenizer and nert_model):
        print("WARNING: NERT model not loaded. Check errors above.")

    print("Starting Flask development server...")
    app.run(debug=True, host='127.0.0.1', port=5000)
