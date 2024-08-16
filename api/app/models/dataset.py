from datetime import datetime
from app.extensions import db


class Dataset(db.Model):
    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(2000), nullable=True)
    size_file = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.TIMESTAMP, default=None, onupdate=datetime.utcnow, nullable=True
    )

    # Chaves estrangeiras
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relacionamentos
    project = db.relationship("Project", back_populates="datasets")
    user = db.relationship("User", back_populates="datasets")
    clean_dataset = db.relationship(
        "CleanDataset", uselist=False, back_populates="dataset"
    )
