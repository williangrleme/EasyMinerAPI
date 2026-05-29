from app.schemas.auth import LoginSchema
from app.schemas.data_mining.classification import ClassificationSchema
from app.schemas.data_mining.cleaning import DataCleaningSchema
from app.schemas.data_mining.normalization import DataNormalizationSchema
from app.schemas.data_mining.reduction import DataReductionSchema
from app.schemas.data_mining.visualization import VisualizationSchema
from app.schemas.dataset import (CleanDatasetReadSchema, DatasetCreateSchema,
                                 DatasetReadSchema, DatasetUpdateSchema)
from app.schemas.project import (DatasetSummarySchema, ProjectCreateSchema,
                                 ProjectDetailSchema, ProjectReadSchema,
                                 ProjectUpdateSchema)
from app.schemas.user import (UserCreateSchema, UserReadSchema,
                              UserUpdateSchema)

_SCHEMAS = [
    LoginSchema,
    UserCreateSchema, UserReadSchema, UserUpdateSchema,
    ProjectCreateSchema, ProjectUpdateSchema, ProjectReadSchema,
    ProjectDetailSchema, DatasetSummarySchema,
    DatasetCreateSchema, DatasetUpdateSchema, DatasetReadSchema, CleanDatasetReadSchema,
    DataCleaningSchema, DataNormalizationSchema, DataReductionSchema,
    ClassificationSchema, VisualizationSchema,
]


def _build_components() -> dict:
    components: dict = {}
    for schema in _SCHEMAS:
        json_schema = schema.model_json_schema(ref_template="#/components/schemas/{model}")
        for name, definition in json_schema.pop("$defs", {}).items():
            components.setdefault(name, definition)
        components[schema.__name__] = json_schema
    return components


def build_swagger_template() -> dict:
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "EasyMinerAPI",
            "version": "2.0.0",
            "description": "API de KDD do EasyMiner — usuários, projetos, bases de dados e algoritmos de mineração.",
        },
        "components": {"schemas": _build_components()},
    }


SWAGGER_CONFIG = {
    "headers": [],
    "specs": [{"endpoint": "apispec", "route": "/apispec.json"}],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}
