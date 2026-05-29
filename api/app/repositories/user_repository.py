from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.session.query(User).filter_by(email=email).first()

    def email_taken(self, email: str, exclude_id: int | None = None) -> bool:
        query = self.session.query(User).filter(User.email == email)
        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)
        return self.session.query(query.exists()).scalar()

    def phone_taken(self, phone: str, exclude_id: int | None = None) -> bool:
        query = self.session.query(User).filter(User.phone_number == phone)
        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)
        return self.session.query(query.exists()).scalar()
