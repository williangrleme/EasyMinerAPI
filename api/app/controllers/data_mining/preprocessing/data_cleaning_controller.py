import pandas as pd
import hashlib
from io import BytesIO
from app.models import Dataset, CleanDataset
from flask_login import current_user
from flask import jsonify
from app.forms.data_mining_forms.preprocessing.data_cleaning_forms import (
    DataCleaningForm,
)
from app.controllers.s3_controller import S3Controller
from app import db
import os


def dataCleaning(id):
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    form = DataCleaningForm(file_url=dataset.file_url)

    if form.validate_on_submit():
        target = form.target.data
        features = form.features.data
        methods = form.methods.data

        # Carrega o arquivo CSV original
        df_original = pd.read_csv(dataset.file_url, na_values="?")

        # Cria uma cópia das colunas selecionadas para limpeza
        df_features = df_original[features].copy()

        # Identifica as colunas com valores faltantes
        columns_missing_value = df_features.columns[df_features.isnull().any()]

        # Aplica o método de substituição de valores faltantes em cada coluna
        for c in columns_missing_value:
            updateMissingValues(df_features, c, methods)

        # Substitui as colunas originais pelas colunas limpas
        df_original.update(df_features)

        # Gera o nome do arquivo com o hash original e o sufixo '_clean'
        file_hash = dataset.file_url.split("/")[-1].replace(".csv", "")
        clean_file_name = f"{file_hash}_clean.csv"

        # Converte o DataFrame para CSV em memória
        csv_buffer = BytesIO()
        df_original.to_csv(csv_buffer, header=True, index=False)
        csv_buffer.seek(0)

        # Calcula o tamanho do arquivo antes do upload
        size_file_with_unit = (
            f"{round(csv_buffer.getbuffer().nbytes / (1024 * 1024), 4)}MB"
        )

        # Faz o upload do arquivo tratado para o S3
        csv_file = BytesIO(csv_buffer.read())  # Prepara o buffer para upload
        csv_file.filename = clean_file_name  # Define o nome do arquivo no S3
        csv_file.content_type = "text/csv"

        s3Controller = S3Controller()
        file_url = s3Controller.upload_file_to_s3(csv_file)

        # Insere os dados na tabela CleanDataset
        clean_dataset = CleanDataset(
            size_file=size_file_with_unit,
            link_file=file_url,
            dataset_id=dataset.id,
            user_id=current_user.id,
        )
        db.session.add(clean_dataset)
        db.session.commit()

        return jsonify({"mensagem": "Limpeza de dados realizada com sucesso!"}), 201

    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def updateMissingValues(df, column, method="mode", number=0):
    if method == "number":
        df[column] = df[column].fillna(number)
    elif method == "median":
        df[column] = df[column].fillna(df[column].median())
    elif method == "mean":
        df[column] = df[column].fillna(df[column].mean())
    elif method == "mode":
        df[column] = df[column].fillna(df[column].mode()[0])
