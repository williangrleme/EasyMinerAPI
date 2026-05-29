import hashlib

from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.common.files import bytes_to_mb_label
from app.config import Config
from app.models import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.project_repository import ProjectRepository


class DatasetService:
    def __init__(self, datasets: DatasetRepository, projects: ProjectRepository, storage):
        self._datasets = datasets
        self._projects = projects
        self._storage = storage

    def list(self, user_id: int) -> list[Dataset]:
        return self._datasets.list_by_user(user_id)

    def get(self, dataset_id: int, user_id: int) -> Dataset:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")
        return dataset

    @transactional
    def create(self, data, csv_file, user_id: int) -> Dataset:
        self._validate_file(csv_file)
        if self._datasets.name_taken(data.name, user_id):
            raise ValidationError("Dados inválidos!", {"name": ["O nome da base de dados já existe."]})
        project = self._projects.get_owned(data.project_id, user_id)
        if not project:
            raise ValidationError("Dados inválidos!", {"project_id": ["O projeto não existe."]})
        size_label, file_url = self._store(csv_file, user_id, data.name)
        return self._datasets.add(Dataset(
            name=data.name, description=data.description, size_file=size_label,
            file_url=file_url, project_id=data.project_id, user_id=user_id,
        ))

    @transactional
    def update(self, dataset_id: int, data, csv_file, user_id: int) -> Dataset:
        dataset = self.get(dataset_id, user_id)
        if data.name and self._datasets.name_taken(data.name, user_id, exclude_id=dataset_id):
            raise ValidationError("Dados inválidos!", {"name": ["O nome da base de dados já existe."]})
        if data.project_id and not self._projects.get_owned(data.project_id, user_id):
            raise ValidationError("Dados inválidos!", {"project_id": ["O projeto não existe."]})
        if csv_file:
            self._validate_file(csv_file)
            size_label, file_url = self._store(csv_file, user_id, data.name or dataset.name)
            dataset.size_file = size_label
            dataset.file_url = file_url
        if data.name:
            dataset.name = data.name
        if data.description:
            dataset.description = data.description
        if data.project_id:
            dataset.project_id = data.project_id
        return dataset

    @transactional
    def delete(self, dataset_id: int, user_id: int) -> Dataset:
        dataset = self.get(dataset_id, user_id)
        if dataset.clean_dataset and dataset.clean_dataset.file_url:
            self._storage.delete(dataset.clean_dataset.file_url)
        if dataset.file_url:
            self._storage.delete(dataset.file_url)
        self._datasets.delete(dataset)
        return dataset

    def _store(self, csv_file, user_id: int, name: str) -> tuple[str, str]:
        csv_file.seek(0, 2)
        size_label = bytes_to_mb_label(csv_file.tell())
        csv_file.seek(0)
        file_hash = hashlib.md5(f"{user_id}_{name}".encode()).hexdigest()
        csv_file.filename = f"{file_hash}.csv"
        url = self._storage.upload(csv_file)
        return size_label, url

    @staticmethod
    def _validate_file(csv_file) -> None:
        if not (csv_file.filename or "").lower().endswith(".csv"):
            raise ValidationError("Dados inválidos!", {"csv_file": ["Apenas arquivos CSV são permitidos."]})
        csv_file.seek(0, 2)
        size = csv_file.tell()
        csv_file.seek(0)
        if size > Config.MAX_CONTENT_LENGTH:
            raise ValidationError("Dados inválidos!", {"csv_file": ["O arquivo excede o tamanho máximo permitido"]})
