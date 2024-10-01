import pandas as pd
from io import BytesIO
from flask_login import current_user
from flask import jsonify
from api.app.models import Dataset
from api.app.forms.data_mining_forms.preprocessing.data_normalization_forms import (
    DataNormalizationForm,
)
from api.app.controllers.s3_controller import S3Controller
from api.app import db
from sklearn.preprocessing import MinMaxScaler, StandardScaler


def dataNormalization(id):
    # Verifica se o usuário está autenticado
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Busca o dataset associado ao ID fornecido e ao usuário atual
    dataset = Dataset.query.filter_by(id=id, user_id=current_user.id).first()
    if not dataset:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    # Obtém o dataset limpo
    clean_dataset = dataset.clean_dataset

    # Inicializa o formulário de normalização de dados com a URL do arquivo
    form = DataNormalizationForm(file_url=clean_dataset.file_url)
    if not form.validate_on_submit():
        return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422

    # Carrega o dataset original a partir da URL
    df_original = pd.read_csv(clean_dataset.file_url)
    features = form.features.data
    methods = form.methods.data

    # Normaliza os dados das colunas especificadas conforme os métodos escolhidos
    for feature in features:
        df_original[feature] = normalize_data(df_original[feature], methods)

    # Salva o dataset normalizado e atualiza a URL e o tamanho do arquivo no banco de dados
    file_url, size_file_with_unit = save_normalized_dataset(
        df_original, clean_dataset.file_url
    )

    clean_dataset.file_url = file_url
    clean_dataset.size_file = size_file_with_unit
    db.session.commit()

    return jsonify({"mensagem": "Normalização de dados realizada com sucesso!"}), 201


def normalize_data(column, method):
    # Dicionário para mapear os métodos de normalização para os escaladores correspondentes
    scalers = {"minmax": MinMaxScaler(), "zscore": StandardScaler()}

    # Obtém o escalador apropriado para o método fornecido
    scaler = scalers.get(method)
    if not scaler:
        raise ValueError(f"Método de normalização desconhecido: {method}")

    # Aplica a normalização e retorna a coluna normalizada
    normalized_column = scaler.fit_transform(column.values.reshape(-1, 1))
    return pd.Series(normalized_column.flatten(), index=column.index)


def save_normalized_dataset(df, original_file_url):
    # Extrai o hash do nome do arquivo original e cria um novo nome para o arquivo normalizado
    file_hash = (
        original_file_url.split("/")[-1].replace(".csv", "").replace("_clean", "")
    )
    normalized_file_name = f"{file_hash}_normalized.csv"

    # Salva o DataFrame normalizado em um buffer de memória como um arquivo CSV
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # Calcula o tamanho do arquivo com unidade
    size_file_with_unit = f"{round(csv_buffer.getbuffer().nbytes / (1024 * 1024), 4)}MB"

    # Cria um novo buffer para o arquivo CSV e define o nome e tipo do conteúdo
    csv_file = BytesIO(csv_buffer.read())
    csv_file.filename = normalized_file_name
    csv_file.content_type = "text/csv"

    # Inicializa o controller S3, remove o arquivo antigo e faz o upload do novo arquivo
    s3 = S3Controller()
    s3.delete_file_from_s3(original_file_url)
    file_url = s3.upload_file_to_s3(csv_file)

    return file_url, size_file_with_unit
