from app.models import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository):
    model = Project

    def list_by_user(self, user_id: int) -> list[Project]:
        return self.session.query(Project).filter_by(user_id=user_id).all()

    def get_owned(self, project_id: int, user_id: int) -> Project | None:
        return self.session.query(Project).filter_by(id=project_id, user_id=user_id).first()

    def name_taken(self, name: str, user_id: int, exclude_id: int | None = None) -> bool:
        query = self.session.query(Project).filter(Project.name == name, Project.user_id == user_id)
        if exclude_id is not None:
            query = query.filter(Project.id != exclude_id)
        return self.session.query(query.exists()).scalar()
