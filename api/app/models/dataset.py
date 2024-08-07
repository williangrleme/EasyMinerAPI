from datetime import datetime
from app.extensions import db


class Dataset(db.Model):
    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(2000), nullable=True)
    target = db.Column(db.String(100), nullable=False)
    size_file = db.Column(db.String(255), nullable=False)
    link_file = db.Column(db.String(255), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.TIMESTAMP, default=None, onupdate=datetime.utcnow, nullable=True
    )

    project = db.relationship("Project", back_populates="datasets")
    user = db.relationship("User", back_populates="datasets")
