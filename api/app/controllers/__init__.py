def register_controllers(app):
    """Registra os blueprints de cada domínio."""
    from app.controllers.auth_controller import auth_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
