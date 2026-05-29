def register_controllers(app):
    """Registra os blueprints de cada domínio."""
    from app.controllers.auth_controller import auth_bp
    from app.controllers.user_controller import user_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
