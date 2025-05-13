import app.response_handlers as response
import numpy as np
import pandas as pd
from app.forms.data_mining_forms.data_visualization_forms import \
    DataVisualizationForm
from app.models import CleanDataset, Dataset
from flask_login import current_user


def frequency_distribution(dataset_id):
    try:
        dataset = (
            Dataset.query.with_entities(Dataset.id, Dataset.file_url, CleanDataset)
            .filter_by(id=dataset_id, user_id=current_user.id)
            .first()
        )
        if not dataset:
            return response.handle_not_found_response("Base de dados não encontrada!")

        form = DataVisualizationForm(file_url=dataset.file_url)

        if not form.validate_on_submit():
            return response.handle_unprocessable_entity(form.errors)

        if form.use_clean_dataset.data:
            if dataset.CleanDataset:
                file_url = dataset.CleanDataset.file_url
            else:
                return response.handle_not_found_response(
                    "Dataset limpo não encontrado!"
                )
        else:
            file_url = dataset.file_url

        results = {}
        for feature in form.features.data:
            results[feature] = get_frequency_distribution(file_url, feature)

        return response.handle_success(
            "Distribuição de frequência realizada com sucesso!",
            results,
        )

    except Exception as e:
        return response.handle_internal_server_error_response(
            e, "Erro ao gerar distribuição de frequência!"
        )


def get_frequency_distribution(file_url, feature):
    try:
        df = pd.read_csv(file_url)
        data = df[feature].dropna().values

        n = len(data)
        k = int(1 + 3.322 * np.log10(n))

        X_max, X_min = max(data), min(data)
        R = X_max - X_min
        h = int(round(float(R / k)))

        bins = np.arange(X_min, X_max + h, h)
        freq, bins = np.histogram(data, bins=bins)

        results = {
            "frequency_distribution": [
                {
                    "interval": f"{int(bins[i])} - {int(bins[i + 1])}",
                    "frequency": int(freq[i]),
                }
                for i in range(len(freq))
            ]
        }
        return results
    except Exception as e:
        raise ValueError(f"Erro ao calcular distribuição de frequência: {e}")
