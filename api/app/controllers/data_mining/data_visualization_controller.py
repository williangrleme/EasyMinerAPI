import app.response_handlers as response
import numpy as np
import pandas as pd
from app.forms.data_mining_forms.data_visualization_forms import \
    DataVisualizationForm
from app.models import CleanDataset, Dataset
from flask_login import current_user


def measure_central_tendency(dataset_id):
    try:
        dataset = (
            Dataset.query.outerjoin(CleanDataset, Dataset.id == CleanDataset.dataset_id)
            .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
            .with_entities(
                Dataset.id,
                Dataset.file_url,
                CleanDataset.file_url.label("clean_file_url"),
            )
            .first()
        )

        if not dataset:
            return response.handle_not_found_response("Base de dados não encontrada!")

        form = DataVisualizationForm(
            file_url=dataset.file_url, method_type="central_tendency"
        )
        if not form.validate_on_submit():
            return response.handle_unprocessable_entity(form.errors)

        if form.use_clean_dataset.data:
            if dataset.clean_file_url:
                file_url = dataset.clean_file_url
            else:
                return response.handle_not_found_response(
                    "Dataset limpo não encontrado!"
                )
        else:
            file_url = dataset.file_url

        visualization_methods = {
            "frequency_distribution": get_frequency_distribution_results,
            "mode": get_mode_results,
            "midpoint": get_midpoint_results,
            "median": get_median_results,
            "weighted_average": get_weighted_average_results,
            "mean_frequency_distribution": get_mean_frequency_distribution_results,
            "geometric_mean": get_geometric_mean_results,
            "harmonic_mean": get_harmonic_mean_results,
        }

        visualization_method = form.visualization_method.data

        method_function = visualization_methods[visualization_method]
        results = method_function(file_url, [f.data for f in form.features])

        return response.handle_success(
            f"Visualização de medidas de tendência central realizada com sucesso!",
            results,
        )

    except Exception as e:
        return response.handle_internal_server_error_response(
            e, f"Erro ao processar visualização de dados!"
        )


def dispersion_measure(dataset_id):
    try:
        dataset = (
            Dataset.query.outerjoin(CleanDataset, Dataset.id == CleanDataset.dataset_id)
            .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
            .with_entities(
                Dataset.id,
                Dataset.file_url,
                CleanDataset.file_url.label("clean_file_url"),
            )
            .first()
        )

        if not dataset:
            return response.handle_not_found_response("Base de dados não encontrada!")

        form = DataVisualizationForm(
            file_url=dataset.file_url, method_type="dispersion"
        )
        if not form.validate_on_submit():
            return response.handle_unprocessable_entity(form.errors)

        if form.use_clean_dataset.data:
            if dataset.clean_file_url:
                file_url = dataset.clean_file_url
            else:
                return response.handle_not_found_response(
                    "Dataset limpo não encontrado!"
                )
        else:
            file_url = dataset.file_url

        visualization_methods = {
            "amplitude": get_amplitude_results,
            "standard_deviation": get_standard_deviation_results,
            "variance": get_variance_results,
            "variation_coefficient": get_variation_coefficient_results,
        }

        visualization_method = form.visualization_method.data

        method_function = visualization_methods[visualization_method]
        results = method_function(file_url, [f.data for f in form.features])

        return response.handle_success(
            f"Visualização de medidas de dispersão realizada com sucesso!",
            results,
        )

    except Exception as e:
        return response.handle_internal_server_error_response(
            e, f"Erro ao processar medidas de dispersão!"
        )


def shape_measure(dataset_id):
    try:
        dataset = (
            Dataset.query.outerjoin(CleanDataset, Dataset.id == CleanDataset.dataset_id)
            .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
            .with_entities(
                Dataset.id,
                Dataset.file_url,
                CleanDataset.file_url.label("clean_file_url"),
            )
            .first()
        )

        if not dataset:
            return response.handle_not_found_response("Base de dados não encontrada!")

        form = DataVisualizationForm(file_url=dataset.file_url, method_type="shape")
        if not form.validate_on_submit():
            return response.handle_unprocessable_entity(form.errors)

        if form.use_clean_dataset.data:
            if dataset.clean_file_url:
                file_url = dataset.clean_file_url
            else:
                return response.handle_not_found_response(
                    "Dataset limpo não encontrado!"
                )
        else:
            file_url = dataset.file_url

        visualization_methods = {
            "skewness": get_skewness_results,
            "kurtosis": get_kurtosis_results,
        }

        visualization_method = form.visualization_method.data

        method_function = visualization_methods[visualization_method]
        results = method_function(file_url, [f.data for f in form.features])

        return response.handle_success(
            f"Visualização de medidas de forma realizada com sucesso!",
            results,
        )

    except Exception as e:
        return response.handle_internal_server_error_response(
            e, f"Erro ao processar medidas de forma!"
        )


def association_measure(dataset_id):
    try:
        dataset = (
            Dataset.query.outerjoin(CleanDataset, Dataset.id == CleanDataset.dataset_id)
            .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
            .with_entities(
                Dataset.id,
                Dataset.file_url,
                CleanDataset.file_url.label("clean_file_url"),
            )
            .first()
        )

        if not dataset:
            return response.handle_not_found_response("Base de dados não encontrada!")

        form = DataVisualizationForm(
            file_url=dataset.file_url, method_type="association"
        )
        if not form.validate_on_submit():
            return response.handle_unprocessable_entity(form.errors)

        if form.use_clean_dataset.data:
            if dataset.clean_file_url:
                file_url = dataset.clean_file_url
            else:
                return response.handle_not_found_response(
                    "Dataset limpo não encontrado!"
                )
        else:
            file_url = dataset.file_url

        visualization_methods = {
            "covariance": get_covariance_results,
            "correlation": get_correlation_results,
        }

        visualization_method = form.visualization_method.data
        features = [f.data for f in form.features]

        if len(features) != 2:
            return response.handle_unprocessable_entity(
                {
                    "features": [
                        "Para medidas de associação é necessário exatamente 2 features."
                    ]
                }
            )

        method_function = visualization_methods[visualization_method]
        results = method_function(file_url, features)

        return response.handle_success(
            f"Visualização de medidas de associação realizada com sucesso!",
            results,
        )

    except Exception as e:
        return response.handle_internal_server_error_response(
            e, f"Erro ao processar medidas de associação!"
        )


def get_frequency_distribution_results(file_url, features):
    results = {}
    for feature in features:
        results[feature] = get_frequency_distribution(file_url, feature)
    return results


def get_mode_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            mode_values = df[feature].mode().tolist()
            results[feature] = mode_values
        else:
            results[feature] = None
    return results


def get_midpoint_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            midpoint_values = round(df[feature].mean(), 2)
            results[feature] = midpoint_values
        else:
            results[feature] = None
    return results


def get_median_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            median_value = df[feature].median()
            results[feature] = median_value
        else:
            results[feature] = None
    return results


def get_weighted_average_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            weighted_avg = np.average(df[feature], weights=df.index + 1)
            results[feature] = round(weighted_avg, 2)
        else:
            results[feature] = None
    return results


def get_mean_frequency_distribution_results(file_url, features):
    results = {}
    for feature in features:
        freq_dist = get_frequency_distribution(file_url, feature)
        results[feature] = calculate_mean_by_class(freq_dist["frequency_distribution"])
    return results


def get_geometric_mean_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            geometric_mean_value = round(
                np.exp(np.log(df[feature].replace(0, np.nan)).mean()), 2
            )
            results[feature] = geometric_mean_value
        else:
            results[feature] = None
    return results


def get_harmonic_mean_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            harmonic_mean_value = round(
                len(df[feature]) / np.sum(1 / df[feature].replace(0, np.nan)), 2
            )
            results[feature] = harmonic_mean_value
        else:
            results[feature] = None
    return results


def get_skewness_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            from scipy import stats

            skewness_value = float(round(stats.skew(df[feature].dropna()), 2))
            results[feature] = skewness_value
        else:
            results[feature] = None
    return results


def get_kurtosis_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            from scipy import stats

            kurtosis_value = float(round(stats.kurtosis(df[feature].dropna()), 2))
            results[feature] = kurtosis_value
        else:
            results[feature] = None
    return results


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


def calculate_mean_by_class(frequency_distribution):
    try:
        class_means = []

        for item in frequency_distribution:
            interval = item["interval"]
            frequency = item["frequency"]

            limits = interval.split(" - ")
            lower_limit = float(limits[0])
            upper_limit = float(limits[1])

            class_mean = (lower_limit + upper_limit) / 2

            class_means.append(
                {
                    "interval": interval,
                    "frequency": frequency,
                    "class_mean": round(class_mean, 2),
                }
            )

        return {
            "frequency_distribution_with_means": class_means,
            "overall_mean": calculate_overall_mean_from_classes(class_means),
        }

    except Exception as e:
        raise ValueError(f"Erro ao calcular média por classe: {e}")


def calculate_overall_mean_from_classes(class_means):
    try:
        total_freq = sum(item["frequency"] for item in class_means)
        if total_freq == 0:
            return 0

        weighted_sum = sum(
            item["class_mean"] * item["frequency"] for item in class_means
        )
        overall_mean = weighted_sum / total_freq

        return round(overall_mean, 2)

    except Exception as e:
        raise ValueError(f"Erro ao calcular média geral: {e}")


def get_amplitude_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            amplitude_value = float(df[feature].max() - df[feature].min())
            results[feature] = amplitude_value
        else:
            results[feature] = None
    return results


def get_standard_deviation_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            std_dev_value = float(round(df[feature].std(), 2))
            results[feature] = std_dev_value
        else:
            results[feature] = None
    return results


def get_variance_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            variance_value = float(round(df[feature].var(), 2))
            results[feature] = variance_value
        else:
            results[feature] = None
    return results


def get_variation_coefficient_results(file_url, features):
    df = pd.read_csv(file_url)
    results = {}
    for feature in features:
        if feature in df.columns:
            variation_coefficient_value = float(
                round((df[feature].std() / df[feature].mean()) * 100, 2)
            )
            results[feature] = variation_coefficient_value
        else:
            results[feature] = None
    return results


def get_covariance_results(file_url, features):
    if len(features) != 2:
        raise ValueError(
            "Para calcular a covariância são necessárias exatamente 2 features."
        )

    df = pd.read_csv(file_url)
    feature1, feature2 = features

    if feature1 not in df.columns or feature2 not in df.columns:
        raise ValueError(
            f"Uma ou mais features não estão presentes no dataset: {feature1}, {feature2}"
        )

    df_clean = df[[feature1, feature2]].dropna()
    covariance_value = float(round(df_clean[feature1].cov(df_clean[feature2]), 4))

    result = {
        "features": f"{feature1} e {feature2}",
        "covariance": covariance_value,
        "feature1_mean": float(round(df_clean[feature1].mean(), 2)),
        "feature2_mean": float(round(df_clean[feature2].mean(), 2)),
        "sample_size": len(df_clean),
        "interpretation": interpret_covariance(covariance_value),
    }

    return result


def get_correlation_results(file_url, features):
    if len(features) != 2:
        raise ValueError(
            "Para calcular a correlação são necessárias exatamente 2 features."
        )

    df = pd.read_csv(file_url)
    feature1, feature2 = features

    if feature1 not in df.columns or feature2 not in df.columns:
        raise ValueError(
            f"Uma ou mais features não estão presentes no dataset: {feature1}, {feature2}"
        )

    df_clean = df[[feature1, feature2]].dropna()
    correlation_value = float(round(df_clean[feature1].corr(df_clean[feature2]), 4))
    covariance_value = float(round(df_clean[feature1].cov(df_clean[feature2]), 4))

    result = {
        "features": f"{feature1} e {feature2}",
        "correlation": correlation_value,
        "covariance": covariance_value,
        "feature1_std": float(round(df_clean[feature1].std(), 2)),
        "feature2_std": float(round(df_clean[feature2].std(), 2)),
        "sample_size": len(df_clean),
        "interpretation": interpret_correlation(correlation_value),
    }

    return result


def interpret_covariance(covariance):
    if covariance > 0:
        return "Covariância positiva: As variáveis tendem a mover-se na mesma direção."
    elif covariance < 0:
        return (
            "Covariância negativa: As variáveis tendem a mover-se em direções opostas."
        )
    else:
        return "Covariância zero: Não há relação linear aparente entre as variáveis."


def interpret_correlation(correlation):
    abs_corr = abs(correlation)
    direction = (
        "positiva" if correlation > 0 else "negativa" if correlation < 0 else "nula"
    )

    if abs_corr >= 0.9:
        strength = "muito forte"
    elif abs_corr >= 0.7:
        strength = "forte"
    elif abs_corr >= 0.5:
        strength = "moderada"
    elif abs_corr >= 0.3:
        strength = "fraca"
    elif abs_corr > 0:
        strength = "muito fraca"
    else:
        strength = "inexistente"

    return (
        f"Correlação {direction} {strength} ({correlation}): "
        + f"As variáveis apresentam uma relação linear {strength}."
    )
