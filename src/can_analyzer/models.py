from flask_sqlalchemy import SQLAlchemy

from .clock import utcnow

db = SQLAlchemy()


class LogFile(db.Model):
    __tablename__ = "log_files"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default="")
    format = db.Column(db.String(8), default="asc")
    frame_count = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=utcnow)


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey("log_files.id"), index=True)
    ts = db.Column(db.Float, default=0.0)
    can_id = db.Column(db.String(16), default="")
    data_hex = db.Column(db.String(64), default="")
    decoded_json = db.Column(db.Text, default="{}")
