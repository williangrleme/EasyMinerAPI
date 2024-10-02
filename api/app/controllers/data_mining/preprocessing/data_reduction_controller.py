import pandas as pd
from io import BytesIO
from flask_login import current_user
from flask import jsonify, current_app
from app.models import Dataset
from api.app.forms.data_mining_forms.preprocessing.data_reduction_forms import (
    DataReductionForm,
)
from sklearn.decomposition import PCA
from app.controllers.s3_controller import S3Controller
from app import db


def dataReduction(id):
    # Verifica se o usuário está autenticado
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Busca o dataset associado ao ID fornecido e ao usuário atual
    dataset = Dataset.query.filter_by(id=id, user_id=current_user.id).first()
    if not dataset:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    # Obtém o dataset limpo
    clean_dataset = dataset.clean_dataset

    # Inicializa o formulário de redução de dados com a URL do arquivo
    form = DataReductionForm(file_url=clean_dataset.file_url)

    # Validação do formulário
    if not form.validate_on_submit():
        return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422

    # Carrega o dataset original a partir da URL
    df = pd.read_csv(clean_dataset.file_url)

    # Extrai os campos do formulário
    features = form.features.data
    methods = form.methods.data

    # Aplica a técnica de redução de dados apropriada
    reduced_df = reduce_data(df, features, methods, form)

    # Loga o DataFrame reduzido para visualização
    current_app.logger.info(f"\nDataset Reduzido:\n{reduced_df.head()}")

    # Salva o dataset reduzido no S3 e atualiza a URL e tamanho no banco de dados
    file_url, size_file_with_unit = save_reduced_dataset(
        reduced_df, clean_dataset.file_url
    )

    # Atualiza o registro do dataset com a nova URL e tamanho
    clean_dataset.file_url = file_url
    clean_dataset.size_file = size_file_with_unit
    db.session.commit()

    # Retorna uma mensagem de sucesso e o dataset reduzido
    return jsonify({"mensagem": "Redução de dados realizada com sucesso!"}), 201


def reduce_data(df, features, method, form):
    # Dicionário para mapear os métodos de redução para as funções correspondentes
    reduction_methods = {
        "pca": apply_pca,
        "amostragem_aleatoria": random_sampling,
        "amostragem_sistematica": systematic_sampling,
    }

    # Obtém a função apropriada para o método fornecido
    reduction_method = reduction_methods.get(method)

    # Executa o método de redução de dados e retorna o DataFrame reduzido
    return reduction_method(df, features, form)


def apply_pca(df, features, form):
    try:
        # Aplica PCA nas features especificadas
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(df[features])

        # Cria um DataFrame com os dois componentes principais
        pca_df = pd.DataFrame(
            pca_result, columns=["Componente Principal 1", "Componente Principal 2"]
        )

        # Retorna o DataFrame reduzido (apenas duas colunas)
        return pca_df
    except Exception as e:
        current_app.logger.error(f"Erro ao aplicar PCA: {e}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro


def random_sampling(df, features, form):
    try:
        n = form.random_records.data

        # Realiza a amostragem aleatória
        sampled_df = df.sample(n=n, replace=False)

        # Retorna o DataFrame reduzido com todas as colunas, mas com as linhas filtradas
        return sampled_df
    except Exception as e:
        current_app.logger.error(f"Erro na amostragem aleatória: {e}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro


def systematic_sampling(df, features, form):
    try:
        n = form.systematic_records.data
        systematic_method = form.systematic_method.data
        feature = features[0]

        # Organiza o dataset de acordo com o critério fornecido
        sorted_df = None
        if systematic_method == "maiores":
            sorted_df = df.nlargest(n, feature)  # Pega os N maiores valores da feature
        elif systematic_method == "menores":
            sorted_df = df.nsmallest(n, feature)  # Pega os N menores valores da feature

        # Retorna o DataFrame reduzido com todas as colunas, mas com as linhas filtradas
        return sorted_df
    except Exception as e:
        current_app.logger.error(f"Erro na amostragem sistemática: {e}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro


def save_reduced_dataset(df, original_file_url):
    # Extrai o hash do nome do arquivo original e remove o sufixo "_clean", se presente
    file_hash = (
        original_file_url.split("/")[-1].replace(".csv", "").replace("_clean", "")
    )
    reduced_file_name = f"{file_hash}_reduced.csv"

    # Salva o DataFrame reduzido em um buffer de memória como um arquivo CSV
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # Calcula o tamanho do arquivo com unidade
    size_file_with_unit = f"{round(csv_buffer.getbuffer().nbytes / (1024 * 1024), 4)}MB"

    # Cria um novo buffer para o arquivo CSV e define o nome e tipo do conteúdo
    csv_file = BytesIO(csv_buffer.read())
    csv_file.filename = reduced_file_name
    csv_file.content_type = "text/csv"

    # Inicializa o controller S3, remove o arquivo antigo e faz o upload do novo arquivo
    s3 = S3Controller()
    s3.delete_file_from_s3(original_file_url)
    file_url = s3.upload_file_to_s3(csv_file)

    return file_url, size_file_with_unit
