def register_controllers(app):
    """Registra os blueprints de cada domínio."""
    from app.controllers.auth_controller import auth_bp
    from app.controllers.dataset_controller import dataset_bp
    from app.controllers.project_controller import project_bp
    from app.controllers.user_controller import user_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(project_bp, url_prefix="/api/projects")
    app.register_blueprint(dataset_bp, url_prefix="/api/datasets")
