from . import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.String(120), primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    transcriptions = db.relationship(
        "Transcription", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    roles = db.relationship(
        "Role", secondary="user_roles", backref=db.backref("users", lazy=True)
    )


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return f"Role('{self.name}')"
    
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.String(120), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id")),
)



class CallDatabase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(50))
    calltext = db.Column(db.String(500), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time = db.Column(db.String(500), nullable=False)


class Transcription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.String(120), db.ForeignKey("user.id"), nullable=False)
    segments = db.relationship(
        "TranscriptionSegment",
        backref="transcription",
        lazy=True,
        cascade="all, delete-orphan",
    )


class TranscriptionSegment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    text = db.Column(db.Text, nullable=False)
    transcription_id = db.Column(
        db.Integer,
        db.ForeignKey("transcription.id", ondelete="CASCADE"),
        nullable=False,
    )
