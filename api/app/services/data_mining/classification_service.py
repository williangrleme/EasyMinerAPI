from app.common.errors import NotFoundError, ValidationError
from app.common.files import read_csv
from app.data_mining.classification.strategies import get_strategy
from app.repositories.clean_dataset_repository import CleanDatasetRepository
from app.repositories.dataset_repository import DatasetRepository


class ClassificationService:
    def __init__(self, datasets: DatasetRepository, clean_datasets: CleanDatasetRepository):
        self._datasets = datasets
        self._clean = clean_datasets

    def classify(self, dataset_id: int, data, user_id: int) -> dict:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")

        file_url = dataset.file_url
        if data.use_clean_dataset:
            clean = self._clean.get_by_dataset(dataset.id)
            if not clean:
                raise NotFoundError("Dataset limpo não encontrado!")
            file_url = clean.file_url

        df = read_csv(file_url)
        if len(df) < 4:
            raise ValidationError("Dados inválidos!", {"dataset": ["O dataset deve ter pelo menos 4 amostras."]})
        invalid = [f for f in data.features if f not in df.columns]
        if invalid:
            raise ValidationError("Dados inválidos!", {"features": [f"Campos não registrados: {', '.join(invalid)}"]})
        if data.target not in df.columns:
            raise ValidationError("Dados inválidos!", {"target": [f"O campo target '{data.target}' não está registrado."]})

        strategy = get_strategy(data.classification_method)
        return strategy.run(df, data.features, data.target, data.model_dump())
