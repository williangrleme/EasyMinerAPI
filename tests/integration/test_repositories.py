from app.repositories.user_repository import UserRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.dataset_repository import DatasetRepository
from tests.factories import make_user, make_project, make_dataset


def test_user_repo_get_by_email(app, db):
    user = make_user(email="a@test.com")
    repo = UserRepository(db.session)
    assert repo.get_by_email("a@test.com").id == user.id
    assert repo.get_by_email("missing@test.com") is None


def test_project_repo_list_by_user(app, db):
    user = make_user()
    make_project(user, name="P1")
    make_project(user, name="P2")
    repo = ProjectRepository(db.session)
    assert len(repo.list_by_user(user.id)) == 2


def test_dataset_repo_get_owned(app, db):
    user = make_user()
    project = make_project(user)
    ds = make_dataset(user, project)
    repo = DatasetRepository(db.session)
    assert repo.get_owned(ds.id, user.id).id == ds.id
    assert repo.get_owned(ds.id, user.id + 999) is None
