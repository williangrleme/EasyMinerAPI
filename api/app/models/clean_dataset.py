from datetime import datetime
from app.extensions import db
from sqlalchemy import event
from app.controllers.s3_controller import S3Controller


class CleanDataset(db.Model):
    __tablename__ = "clean_datasets"
    id = db.Column(db.Integer, primary_key=True)
    size_file = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    dataset_id = db.Column(
        db.Integer, db.ForeignKey("datasets.id"), nullable=False, unique=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=None, onupdate=datetime.utcnow)

    # Relacionamentos
    dataset = db.relationship("Dataset", back_populates="clean_dataset")
    user = db.relationship("User", back_populates="clean_datasets")


# Função que será chamada após a exclusão de um CleanDataset
def delete_clean_dataset_file(mapper, connection, target):
    if target.file_url:
        s3Controller = S3Controller()
        s3Controller.delete_file_from_s3(target.file_url)


# Liga o evento `after_delete` ao modelo `CleanDataset`
event.listen(CleanDataset, "after_delete", delete_clean_dataset_file)
