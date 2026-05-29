from app.models import CleanDataset
from app.repositories.base import BaseRepository


class CleanDatasetRepository(BaseRepository):
    model = CleanDataset

    def get_by_dataset(self, dataset_id: int) -> CleanDataset | None:
        return self.session.query(CleanDataset).filter_by(dataset_id=dataset_id).first()
