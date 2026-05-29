from app.common.errors import NotFoundError, ValidationError
from app.data_mining.visualization.measures import ASSOCIATION, CENTRAL_TENDENCY, DISPERSION, SHAPE
from app.repositories.clean_dataset_repository import CleanDatasetRepository
from app.repositories.dataset_repository import DatasetRepository

_GROUPS = {
    "central_tendency": CENTRAL_TENDENCY,
    "dispersion": DISPERSION,
    "shape": SHAPE,
    "association": ASSOCIATION,
}


class VisualizationService:
    def __init__(self, datasets: DatasetRepository, clean_datasets: CleanDatasetRepository):
        self._datasets = datasets
        self._clean = clean_datasets

    def measure(self, group: str, dataset_id: int, data, user_id: int) -> dict:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")

        registry = _GROUPS[group]
        method = registry.get(data.visualization_method)
        if method is None:
            raise ValidationError("Dados inválidos!", {"visualization_method": [f"Método '{data.visualization_method}' não é válido para {group}."]})

        if group == "association" and len(data.features) != 2:
            raise ValidationError("Dados inválidos!", {"features": ["Para medidas de associação é necessário exatamente 2 features."]})

        file_url = dataset.file_url
        if data.use_clean_dataset:
            clean = self._clean.get_by_dataset(dataset.id)
            if not clean:
                raise NotFoundError("Dataset limpo não encontrado!")
            file_url = clean.file_url

        return method(file_url, data.features)
