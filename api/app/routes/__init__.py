from flask import Blueprint


def init_routes(app):
    from .user_routes import user_bp
    from .auth_routes import auth_bp
    from .project_routes import project_bp
    from .dataset_routes import dataset_bp
    from .data_minig_routes.preprocessing_routes import preprocessing_bp

    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(project_bp, url_prefix="/api/projects")
    app.register_blueprint(dataset_bp, url_prefix="/api/datasets")
    app.register_blueprint(preprocessing_bp, url_prefix="/api/preprocessing")
