import pandas as pd
from io import BytesIO
from api.app.models import Dataset, CleanDataset
from flask_login import current_user
from flask import jsonify
from api.app.forms.data_mining_forms.preprocessing.data_cleaning_forms import (
    DataCleaningForm,
)
from api.app.controllers.s3_controller import S3Controller
from api.app import db


def dataCleaning(id):
    # Verifica se o usuário está autenticado
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Busca o dataset pelo ID e valida se pertence ao usuário atual
    dataset = (
        Dataset.query.with_entities(Dataset.id, Dataset.file_url)
        .filter_by(id=id, user_id=current_user.id)
        .first()
    )
    if dataset is None:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    form = DataCleaningForm(file_url=dataset.file_url)
    if form.validate_on_submit():
        features = form.features.data
        methods = form.methods.data

        # Carrega o arquivo CSV original no DataFrame
        df_original = pd.read_csv(dataset.file_url)

        # Cria uma cópia apenas das colunas selecionadas (features) para limpeza
        df_features = df_original[features].copy()

        # Identifica colunas com valores faltantes ou específicos para tratamento
        columns_missing_value = identify_columns_with_missing_values(df_features)

        # Aplica os métodos de substituição de valores faltantes em cada coluna
        for column in columns_missing_value:
            update_missing_values(df_features, column, methods)

        # Atualiza o DataFrame original com os dados limpos
        df_original.update(df_features)

        # Gera o nome do arquivo limpo e salva no S3
        file_url, size_file_with_unit = save_clean_dataset(
            df_original, dataset.file_url
        )

        # Cria uma nova entrada no banco de dados para o dataset limpo
        clean_dataset = CleanDataset(
            size_file=size_file_with_unit,
            file_url=file_url,
            dataset_id=dataset.id,
            user_id=current_user.id,
        )
        db.session.add(clean_dataset)
        db.session.commit()

        return jsonify({"mensagem": "Limpeza de dados realizada com sucesso!"}), 201

    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def identify_columns_with_missing_values(df):
    return [
        column
        for column in df.columns
        if df[column].isnull().any()
        or (df[column] == "").any()
        or (df[column] == "?").any()
        or (df[column] == 0).any()
    ]


def update_missing_values(df, column, method):
    # Converte valores específicos para NaN
    df[column].replace(["", "?"], pd.NA, inplace=True)

    # Preenche valores faltantes com a estratégia escolhida
    if method == "mediana":
        df[column] = df[column].fillna(df[column].median())
    elif method == "media":
        df[column] = df[column].fillna(df[column].mean())
    elif method == "moda":
        df[column] = df[column].fillna(df[column].mode()[0])


def save_clean_dataset(df, original_file_url):
    # Gera um nome de arquivo único para o dataset limpo usando o hash do arquivo original
    file_hash = original_file_url.split("/")[-1].replace(".csv", "")
    clean_file_name = f"{file_hash}_clean.csv"

    # Converte o DataFrame limpo para CSV em memória para upload
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, header=True, index=False)
    csv_buffer.seek(0)  # Reseta o ponteiro do buffer para o início

    # Calcula o tamanho do arquivo CSV limpo para armazenamento no banco de dados
    size_file_with_unit = f"{round(csv_buffer.getbuffer().nbytes / (1024 * 1024), 4)}MB"

    # Prepara o buffer para upload ao S3 e define metadados
    csv_file = BytesIO(csv_buffer.read())
    csv_file.filename = clean_file_name
    csv_file.content_type = "text/csv"

    # Faz o upload do arquivo limpo para o S3
    s3Controller = S3Controller()
    file_url = s3Controller.upload_file_to_s3(csv_file)

    return file_url, size_file_with_unit
