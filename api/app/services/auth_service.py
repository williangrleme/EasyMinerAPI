from flask_login import login_user, logout_user

from app.common.errors import UnauthorizedError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginSchema


class AuthService:
    def __init__(self, users: UserRepository):
        self._users = users

    def login(self, data: LoginSchema) -> User:
        user = self._users.get_by_email(data.email)
        if not user or not user.check_password(data.password):
            raise UnauthorizedError("Credenciais inválidas!")
        login_user(user)
        return user

    def logout(self) -> None:
        logout_user()
