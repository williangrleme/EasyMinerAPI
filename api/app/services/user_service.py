from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.models import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, users: UserRepository, storage):
        self._users = users
        self._storage = storage

    @transactional
    def create(self, data) -> User:
        self._ensure_unique(data.email, data.phone_number)
        user = User(name=data.name, phone_number=data.phone_number, email=data.email)
        user.set_password(data.password)
        return self._users.add(user)

    @transactional
    def update(self, user_id: int, data) -> User:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado!")
        if data.email and data.email != user.email:
            if self._users.email_taken(data.email, exclude_id=user_id):
                raise ValidationError("Dados inválidos!", {"email": ["E-mail já cadastrado."]})
            user.email = data.email
        if data.phone_number and data.phone_number != user.phone_number:
            if self._users.phone_taken(data.phone_number, exclude_id=user_id):
                raise ValidationError("Dados inválidos!", {"phone_number": ["Número de telefone já cadastrado."]})
            user.phone_number = data.phone_number
        if data.name:
            user.name = data.name
        if data.password:
            user.set_password(data.password)
        return user

    @transactional
    def delete(self, user_id: int) -> User:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado!")
        for dataset in list(user.datasets):
            if dataset.file_url:
                self._storage.delete(dataset.file_url)
        for clean in list(user.clean_datasets):
            if clean.file_url:
                self._storage.delete(clean.file_url)
        self._users.delete(user)
        return user

    def _ensure_unique(self, email: str, phone: str) -> None:
        errors = {}
        if self._users.email_taken(email):
            errors["email"] = ["E-mail já cadastrado."]
        if self._users.phone_taken(phone):
            errors["phone_number"] = ["Número de telefone já cadastrado."]
        if errors:
            raise ValidationError("Dados inválidos!", errors)
