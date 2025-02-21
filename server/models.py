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
    roles = db.relationship("Role", secondary="user_roles", backref="users")
    def has_role(self, role_name):
        return self.roles.filter_by(name=role_name).first() is not None


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    
    def __repr__(self):
        return f"Role('{self.name}')"

class UserRoles(db.Model):
    __table_args__ = (db.PrimaryKeyConstraint('user_id', 'role_id'),)
    user_id = db.Column(db.String(120), db.ForeignKey("user.id"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)

    user = db.relationship("User", backref=db.backref("user_roles", cascade="delete"))
    def __repr__(self):
        return f"UserRoles('{self.user_id}', '{self.role_id}')"



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
