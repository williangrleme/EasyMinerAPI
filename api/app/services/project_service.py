from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.models import Project
from app.repositories.project_repository import ProjectRepository


class ProjectService:
    def __init__(self, projects: ProjectRepository, storage):
        self._projects = projects
        self._storage = storage

    def list(self, user_id: int) -> list[Project]:
        return self._projects.list_by_user(user_id)

    def get(self, project_id: int, user_id: int) -> Project:
        project = self._projects.get_owned(project_id, user_id)
        if not project:
            raise NotFoundError("Projeto não encontrado!")
        return project

    @transactional
    def create(self, data, user_id: int) -> Project:
        if self._projects.name_taken(data.name, user_id):
            raise ValidationError("Dados inválidos!", {"name": ["O nome do projeto já existe."]})
        return self._projects.add(Project(name=data.name, description=data.description, user_id=user_id))

    @transactional
    def update(self, project_id: int, data, user_id: int) -> Project:
        project = self.get(project_id, user_id)
        if data.name and data.name != project.name:
            if self._projects.name_taken(data.name, user_id, exclude_id=project_id):
                raise ValidationError("Dados inválidos!", {"name": ["O nome do projeto já existe."]})
            project.name = data.name
        if data.description:
            project.description = data.description
        return project

    @transactional
    def delete(self, project_id: int, user_id: int) -> Project:
        project = self.get(project_id, user_id)
        for dataset in list(project.datasets):
            if dataset.file_url:
                self._storage.delete(dataset.file_url)
            if dataset.clean_dataset and dataset.clean_dataset.file_url:
                self._storage.delete(dataset.clean_dataset.file_url)
        self._projects.delete(project)
        return project
