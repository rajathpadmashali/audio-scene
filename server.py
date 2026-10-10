import os
import uuid
import json
import warnings
from pathlib import Path

# Suppress pyloudnorm clipping warnings
warnings.filterwarnings("ignore", message="Possible clipped samples in output.")
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models import db, User, AudioBook, Follow

# Audio pipeline imports
from parser import parse_script, generate_script_from_prompt
from tts import generate_tts
from ambient import get_ambient_clip, get_music_clip
from mixer.mix import mix_scene
from translator import apply_translation

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.before_request
def create_tables():
    app.before_request_funcs[None].remove(create_tables)
    db.create_all()
    # Ensure admin user exists with username 'admin' and password 'admin'
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin'),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
    else:
        admin_user.is_admin = True
        admin_user.password_hash = generate_password_hash('admin')
        db.session.commit()

@app.route('/')
def index():
    return redirect(url_for('explore'))


@app.route('/my_audios')
@login_required
def my_audios():
    books = AudioBook.query.filter_by(user_id=current_user.id).order_by(AudioBook.created_at.desc()).all()
    return render_template('explore.html', books=books, title="My Audiobooks")

@app.route('/explore')

def explore():
    books = AudioBook.query.order_by(AudioBook.created_at.desc()).all()
    return render_template('explore.html', books=books, title="Explore All")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        is_admin = False
        if User.query.count() == 0:
            is_admin = True # First user is admin
            
        new_user = User(
            username=username, 
            password_hash=generate_password_hash(password),
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/follow/<int:user_id>')
@login_required
def follow(user_id):
    user = db.get_or_404(User, user_id)
    if user != current_user:
        current_user.follow(user)
        db.session.commit()
        flash(f'You are now following {user.username}')
    return redirect(request.referrer or url_for('index'))

@app.route('/unfollow/<int:user_id>')
@login_required
def unfollow(user_id):
    user = db.get_or_404(User, user_id)
    if user != current_user:
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You unfollowed {user.username}')
    return redirect(request.referrer or url_for('index'))

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        prompt = request.form.get('prompt', '').strip()
        theme = request.form.get('theme', 'Mystery')
        language = request.form.get('language', 'English')
        mode = request.form.get('mode', 'AI')
        
        if not prompt:
            flash('Please enter a valid prompt.')
            return redirect(url_for('create'))
            
        try:
            if mode == 'Manual':
                # User wrote the full story, just let the parser extract scene
                script_text = prompt
            elif theme == 'Study' or mode == 'Study':
                full_prompt = f"Create an educational and engaging discussion between 2 or more people in {language} who discuss the topic '{prompt}'. They should explain the concept clearly to help the listener understand it."
                script_text = generate_script_from_prompt(full_prompt)
            else:
                # Add the theme and language heavily to the prompt
                full_prompt = f"Write a scene in {language}, in a {theme} style. {prompt}"
                script_text = generate_script_from_prompt(full_prompt)
            
            # Map full language names to codes
            lang_code_map = {'English': 'en', 'Hindi': 'hi', 'Kannada': 'kn'}
            lang_code = lang_code_map.get(language, 'en')

            # 2. Parse Script
            scene = parse_script(script_text, 'auto')
            
            # If the user manually wrote the script, override the language with the dropdown choice
            if mode == 'Manual':
                scene.language = lang_code
                
            apply_translation(scene)
            
            # Ensure the selected theme is in the background_scene so models.py infers the correct folder
            # Only do this if we are not relying purely on taxonomy labels for ambient clip lookups.
            # Wait, get_ambient_clip uses ESC50_TAXONOMY labels strictly! So prepending theme breaks get_ambient_clip!
            # We should keep scene.background_scene clean for get_ambient_clip to work.
            
            clean_bg = scene.background_scene
            
            # 3. Generate TTS
            tts_results = []
            emotions = []
            for d in scene.dialogues:
                res = generate_tts(d.text, scene.language, d.gender, d.emotion, d.idx, d.speaker)
                tts_results.append(res)
                emotions.append(d.emotion)
                
            # 4. Background and Mix
            dominant = max(set(emotions), key=emotions.count) if emotions else "neutral"
            
            # Handle manual ambient selection
            ambient_selection = request.form.get('ambient', 'AI Recommended')
            if ambient_selection == 'AI Recommended':
                ambient_path = get_ambient_clip(clean_bg)
            elif ambient_selection == 'None':
                ambient_path = None
            else:
                # ambient_selection here is probably a friendly name from UI.
                # Assuming UI sends valid labels, but if not we should ensure valid.
                ambient_path = get_ambient_clip(ambient_selection.lower().replace(" ", "_"))
                
            music_path = get_music_clip(dominant)
            
            # Ensure the selected theme is in the background_scene so models.py infers the correct folder
            if theme.lower() not in scene.background_scene.lower():
                scene.background_scene = f"{theme.title()} - {scene.background_scene}"
                
            uid = str(uuid.uuid4())
            wav_filename = f"{uid}.wav"
            json_filename = f"{uid}.json"
            
            out_path = os.path.join('static', 'audio', wav_filename)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            mix_scene(scene, tts_results, ambient_path, music_path, out_path)
            
            # Save to DB
            book = AudioBook(
                title=prompt[:50] + "...",
                file_path=f"audio/{wav_filename}",
                timeline_path=f"audio/{json_filename}",
                scene_json=scene.model_dump_json(),
                user_id=current_user.id
            )
            db.session.add(book)
            db.session.commit()
            
            flash('AudioBook successfully created!')
            return redirect(url_for('view_book', book_id=book.id))
            
        except Exception as e:
            flash(f'Error creating audiobook: {str(e)}')
            return redirect(url_for('create'))
            
    return render_template('create.html')


@app.route('/delete_book/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    book = db.get_or_404(AudioBook, book_id)
    if book.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized to delete this audio.')
        return redirect(url_for('explore'))
        
    try:
        wav_path = os.path.join('static', book.file_path)
        json_path = os.path.join('static', book.timeline_path)
        if os.path.exists(wav_path): os.remove(wav_path)
        if os.path.exists(json_path): os.remove(json_path)
    except:
        pass
        
    db.session.delete(book)
    db.session.commit()
    flash('Audio successfully deleted.')
    return redirect(request.referrer or url_for('profile', user_id=current_user.id))

@app.route('/book/<int:book_id>')

def view_book(book_id):
    book = db.get_or_404(AudioBook, book_id)
    scene_data = json.loads(book.scene_json)
    
    # Need to load the timeline to inject into template
    timeline_path = os.path.join('static', book.timeline_path)
    timeline_data = []
    if os.path.exists(timeline_path):
        with open(timeline_path, 'r') as f:
            timeline_data = json.load(f)
            
    return render_template('book.html', book=book, scene=scene_data, timeline=timeline_data)


@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = db.get_or_404(User, user_id)
    books = AudioBook.query.filter_by(user_id=user.id).order_by(AudioBook.created_at.desc()).all()
    return render_template('profile.html', user=user, books=books)


@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash("Unauthorized access.")
        return redirect(url_for('index'))
    books = AudioBook.query.all()
    return render_template('admin.html', books=books)

@app.route('/admin/delete_all', methods=['POST'])
@login_required
def admin_delete_all():
    if not current_user.is_admin:
        flash("Unauthorized.")
        return redirect(url_for('index'))
    
    books = AudioBook.query.all()
    for book in books:
        try:
            wav_path = os.path.join('static', book.file_path)
            json_path = os.path.join('static', book.timeline_path)
            if os.path.exists(wav_path): os.remove(wav_path)
            if os.path.exists(json_path): os.remove(json_path)
        except:
            pass
        db.session.delete(book)
    db.session.commit()
    flash("All audios have been successfully deleted.")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
