from datetime import datetime

from app.extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(2000), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.TIMESTAMP, default=None, onupdate=datetime.utcnow, nullable=True
    )

    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relacionamentos
    user = db.relationship("User", back_populates="projects")
    datasets = db.relationship(
        "Dataset", back_populates="project", cascade="all, delete-orphan"
    )
