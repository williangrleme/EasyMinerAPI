import pandas as pd

from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.common.files import dataframe_to_csv_upload, read_csv
from app.data_mining.cleaning.strategies import get_strategy
from app.models import CleanDataset
from app.repositories.clean_dataset_repository import CleanDatasetRepository
from app.repositories.dataset_repository import DatasetRepository

_MISSING_MAP = {"null": None, "0": 0, "?": "?", "": None}


class DataCleaningService:
    def __init__(self, datasets: DatasetRepository, clean_datasets: CleanDatasetRepository, storage):
        self._datasets = datasets
        self._clean = clean_datasets
        self._storage = storage

    @transactional
    def clean(self, dataset_id: int, data, user_id: int) -> CleanDataset:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")

        df_original = read_csv(dataset.file_url)
        self._validate_features(df_original, data.features)
        df_clean = self._apply(df_original, data)

        filename = f"{dataset.file_url.split('/')[-1].split('.')[0]}_clean.csv"
        upload, size_label = dataframe_to_csv_upload(df_clean, filename)
        file_url = self._storage.upload(upload)

        existing = self._clean.get_by_dataset(dataset.id)
        if existing:
            if existing.file_url:
                self._storage.delete(existing.file_url)
            self._clean.delete(existing)

        return self._clean.add(CleanDataset(
            size_file=size_label, file_url=file_url, dataset_id=dataset.id, user_id=user_id,
        ))

    def _apply(self, df, data):
        missing = [_MISSING_MAP.get(v, v) for v in data.missing_values]
        strategy = get_strategy(data.methods)
        result = df.copy()
        for column in data.features:
            result[column] = result[column].replace(missing, pd.NA)
            result[column] = strategy.apply(pd.to_numeric(result[column], errors="coerce"))
        return result

    @staticmethod
    def _validate_features(df, features):
        invalid = [f for f in features if f not in df.columns]
        if invalid:
            raise ValidationError("Dados inválidos!", {"features": [f"Campos não registrados: {', '.join(invalid)}"]})
