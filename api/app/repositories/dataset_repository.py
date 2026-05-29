from app.models import Dataset
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository):
    model = Dataset

    def list_by_user(self, user_id: int) -> list[Dataset]:
        return self.session.query(Dataset).filter_by(user_id=user_id).all()

    def get_owned(self, dataset_id: int, user_id: int) -> Dataset | None:
        return self.session.query(Dataset).filter_by(id=dataset_id, user_id=user_id).first()

    def name_taken(self, name: str, user_id: int, exclude_id: int | None = None) -> bool:
        query = self.session.query(Dataset).filter(Dataset.name == name, Dataset.user_id == user_id)
        if exclude_id is not None:
            query = query.filter(Dataset.id != exclude_id)
        return self.session.query(query.exists()).scalar()
