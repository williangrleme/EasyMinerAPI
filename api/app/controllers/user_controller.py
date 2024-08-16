from flask import jsonify, current_app
from flask_login import current_user
from app.models import User
from app import db
from app.forms.user_form import UserFormCreate, UserFormUpdate


def get_users():
    user_master = current_app.config["USER_MASTER"]
    if not current_user.is_authenticated or current_user.id != user_master:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    users = User.query.with_entities(
        User.id, User.name, User.phone_number, User.email
    ).all()
    users_list = [
        {
            "id": user.id,
            "name": user.name,
            "phone_number": user.phone_number,
            "email": user.email,
        }
        for user in users
    ]
    return jsonify(users_list), 200


def get_user(id):
    if not current_user.is_authenticated or current_user.id != id:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    user = (
        User.query.with_entities(User.id, User.name, User.phone_number, User.email)
        .filter_by(id=id)
        .first()
    )
    if user is None:
        return jsonify({"mensagem": "Usuário não encontrado!"}), 404

    user_data = {
        "id": user.id,
        "name": user.name,
        "phone_number": user.phone_number,
        "email": user.email,
    }
    return jsonify(user_data), 200


def create_user():
    form = UserFormCreate()
    if form.validate_on_submit():
        new_user = User(
            name=form.name.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"mensagem": "Usuário criado com sucesso!"}), 201
    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def update_user(id):
    if not current_user.is_authenticated or current_user.id != id:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    user = User.query.get(id)
    if user is None:
        return jsonify({"mensagem": "Usuário não encontrado!"}), 404

    form = UserFormUpdate(user_id=id, obj=user)
    if form.validate_on_submit():
        updated = False
        for field_name, field in form._fields.items():
            if field.data and getattr(user, field_name) != field.data:
                setattr(user, field_name, field.data)
                updated = True
        if form.password.data and not user.check_password(form.password.data):
            user.set_password(form.password.data)
            updated = True
        if updated:
            db.session.commit()
        return jsonify({"mensagem": "Usuário atualizado com sucesso!"}), 200

    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def delete_user(id):
    if not current_user.is_authenticated or current_user.id != id:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return jsonify({"mensagem": "Usuário deletado com sucesso!"}), 200
