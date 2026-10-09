from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationship to audiobooks
    audiobooks = db.relationship('AudioBook', backref='author', lazy=True)
    
    # Relationships for following
    followed = db.relationship(
        'User', secondary='follows',
        primaryjoin=(Follow.follower_id == id),
        secondaryjoin=(Follow.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def is_following(self, user):
        return self.followed.filter(Follow.followed_id == user.id).count() > 0

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

class AudioBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(300), nullable=False) # e.g. static/audio/123.wav
    timeline_path = db.Column(db.String(300), nullable=False) # e.g. static/audio/123.json
    scene_json = db.Column(db.Text, nullable=True) # Full SceneSpec as JSON string for avatars
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    @property
    def theme(self):
        import json
        try:
            data = json.loads(self.scene_json)
            bg = data.get('background_scene', '').lower()
            themes = ['scifi', 'mystery', 'fantasy', 'romance', 'horror', 'comedy', 'thriller', 'drama']
            for t in themes:
                if t in bg: return t
            if 'magic' in bg: return 'fantasy'
            if 'noir' in bg: return 'mystery'
            if 'space' in bg: return 'scifi'
            if 'spooky' in bg: return 'horror'
        except:
            pass
        themes = ['scifi', 'mystery', 'fantasy', 'romance', 'horror', 'comedy', 'thriller', 'drama']
        return themes[self.id % len(themes)] if self.id else 'drama'
