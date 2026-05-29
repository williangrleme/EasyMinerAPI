from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.common.files import dataframe_to_csv_upload, read_csv
from app.data_mining.reduction.strategies import get_strategy
from app.models import CleanDataset
from app.repositories.clean_dataset_repository import CleanDatasetRepository
from app.repositories.dataset_repository import DatasetRepository


class DataReductionService:
    def __init__(self, datasets: DatasetRepository, clean_datasets: CleanDatasetRepository, storage):
        self._datasets = datasets
        self._clean = clean_datasets
        self._storage = storage

    @transactional
    def reduce(self, dataset_id: int, data, user_id: int) -> CleanDataset:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")

        existing = self._clean.get_by_dataset(dataset.id)
        source_url = existing.file_url if existing else dataset.file_url

        df = read_csv(source_url)
        invalid = [f for f in data.features if f not in df.columns]
        if invalid:
            raise ValidationError("Dados inválidos!", {"features": [f"Campos não registrados: {', '.join(invalid)}"]})

        strategy = get_strategy(data.methods)
        reduced = strategy.reduce(df, data.features, data.model_dump())

        base_name = dataset.file_url.split("/")[-1].split(".")[0].split("_")[0]
        upload, size_label = dataframe_to_csv_upload(reduced, f"{base_name}_reduced.csv")
        file_url = self._storage.upload(upload)

        if existing:
            if existing.file_url:
                self._storage.delete(existing.file_url)
            self._clean.delete(existing)

        return self._clean.add(CleanDataset(
            size_file=size_label, file_url=file_url, dataset_id=dataset.id, user_id=user_id,
        ))
