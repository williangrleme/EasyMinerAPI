from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.TIMESTAMP, default=None, onupdate=datetime.utcnow, nullable=True
    )

    # Relacionamentos
    projects = db.relationship(
        "Project", back_populates="user", cascade="all, delete-orphan"
    )
    datasets = db.relationship(
        "Dataset", back_populates="user", cascade="all, delete-orphan"
    )
    clean_datasets = db.relationship(
        "CleanDataset", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        # Retorna True para indicar que o usuário está ativo
        return True

    @property
    def is_authenticated(self):
        # Retorna True se o usuário estiver autenticado
        return True

    @property
    def is_anonymous(self):
        # Retorna False para indicar que o usuário não é anônimo
        return False

    def get_id(self):
        return str(self.id)
