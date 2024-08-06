from flask import Blueprint

def init_routes(app):
    from app.routes.user_routes import user_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.project_routes import project_bp

    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(project_bp, url_prefix="/api/projects")
