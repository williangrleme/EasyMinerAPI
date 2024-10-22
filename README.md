# EasyMinerAPI

Repositório para o back-end da aplicação EasyMiner.

## Descrição
EasyMiner é uma aplicação desenvolvida para facilitar a execução de algoritmos de KDD (Knowledge Discovery in Databases) em conjuntos de dados.
A aplicação é composta por uma API (repositório atual) e uma interface web.

A API gerencia operações relacionadas a usuários, projetos, datasets e algoritmos de KDD.


## Tecnologias Utilizadas

- Amazon S3
- Docker
- Flask
- Python
- SQLAlchemy
- Swagger

## Fluxo de Funcionamento
O fluxo de dados e operações dentro do EasyMinerAPI é ilustrado a seguir:

1. **Rota**: Ponto de entrada onde as requisições são recebidas.
2. **Controller**: Lógica de negócio e coordenação das operações necessárias.
3. **Form Request**: Validação dos dados de entrada.
4. **Model**: Interação com o banco de dados para manipulação das informações.
5. **Banco de Dados**: Armazena os dados estruturados dos conjuntos de dados.
6. **Retorno da API**: Resposta ao cliente com os resultados do processamento.

## Instalação

1. Clone o repositório:
    ```sh
    git clone https://github.com/seu-usuario/EasyMinerAPI.git
    cd EasyMinerAPI
    ```

2. Crie um ambiente virtual e ative-o:
    ```sh
    python -m venv venv
    source venv/bin/activate  # No Windows use `venv\Scripts\activate`
    ```

3. Instale as dependências:
    ```sh
    pip install -r requirements.txt
    ```

4. Configure as variáveis de ambiente necessárias (exemplo para Unix):
    ```sh
   export FLASK_APP=run.py
   export FLASK_ENV=development
   export SECRET_KEY=sua_chave_secreta
   export SQLALCHEMY_DATABASE_URI=sua_uri_do_banco_de_dados
   export S3_BUCKET=seu_bucket_s3
   export S3_KEY=sua_chave_s3
   export S3_SECRET=seu_segredo_s3
    ```
   
5. Execute a aplicação:
    ```sh
    flask run
    ```

## Documentação da API

Para detalhes completos sobre as requisições da API, acesse [aqui](https://easyminerapi.fly.dev/apidocs).

