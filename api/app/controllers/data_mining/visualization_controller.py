from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.data_mining.visualization import VisualizationSchema

visualization_bp = Blueprint("data-visualization", __name__)

_ROUTES = {
    "measure-central-tendency": ("central_tendency", "tendência central"),
    "dispersion-measure": ("dispersion", "dispersão"),
    "shape-measure": ("shape", "forma"),
    "association-measure": ("association", "associação"),
}


def _make_handler(group, label):
    @handle_errors
    def handler(dataset_id):
        """Executa medida de visualização no dataset.
        ---
        tags:
          - Visualization
        requestBody:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VisualizationSchema'
        responses:
          200:
            description: Visualização realizada com sucesso
          401:
            description: Não autorizado
          404:
            description: Dataset não encontrado
        """
        data = VisualizationSchema.model_validate(request.get_json(silent=True) or {})
        results = current_app.services["visualization"].measure(group, dataset_id, data, current_user.id)
        body, status = success_payload(f"Visualização de medidas de {label} realizada com sucesso!", results)
        return jsonify(body), status

    handler.__name__ = f"viz_{group}"
    return handler


for _path, (_group, _label) in _ROUTES.items():
    visualization_bp.add_url_rule(
        f"/{_path}/<int:dataset_id>",
        view_func=login_required(_make_handler(_group, _label)),
        methods=["POST"],
    )
