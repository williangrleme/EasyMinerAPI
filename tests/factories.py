from app.extensions import db
from app.models import Dataset, Project, User


def make_user(email="user@test.com", phone="11999990000", password="senha1234"):
    user = User(name="Usuario De Teste", phone_number=phone, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def make_project(user, name="Projeto Teste"):
    project = Project(name=name, description="descricao do projeto", user_id=user.id)
    db.session.add(project)
    db.session.commit()
    return project


def make_dataset(user, project, name="Base Teste", file_url="https://test-bucket.s3.amazonaws.com/abc.csv"):
    dataset = Dataset(
        name=name, description="descricao base", size_file="0.01MB",
        file_url=file_url, project_id=project.id, user_id=user.id,
    )
    db.session.add(dataset)
    db.session.commit()
    return dataset
