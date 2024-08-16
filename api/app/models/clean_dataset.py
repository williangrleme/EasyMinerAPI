from datetime import datetime
from app.extensions import db


class CleanDataset(db.Model):
    __tablename__ = "clean_datasets"
    id = db.Column(db.Integer, primary_key=True)
    size_file = db.Column(db.String(255), nullable=False)
    link_file = db.Column(db.String(255), nullable=False)
    dataset_id = db.Column(
        db.Integer, db.ForeignKey("datasets.id"), nullable=False, unique=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=None, onupdate=datetime.utcnow)

    # Relacionamentos

    dataset = db.relationship("Dataset", back_populates="clean_dataset")
    user = db.relationship("User", back_populates="clean_datasets")
