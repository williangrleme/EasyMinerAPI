from abc import ABC, abstractmethod

import pandas as pd
from sklearn.decomposition import PCA

from app.common.errors import ValidationError


class ReductionStrategy(ABC):
    name: str

    @abstractmethod
    def reduce(self, df: pd.DataFrame, features: list[str], params: dict) -> pd.DataFrame: ...


class PCAStrategy(ReductionStrategy):
    name = "pca"

    def reduce(self, df, features, params):
        target = params.get("target")
        if not target or target not in df.columns:
            raise ValidationError("Dados inválidos!", {"target": [f"A coluna target '{target}' não está registrada."]})
        if len(features) < 2:
            raise ValidationError("Dados inválidos!", {"features": ["PCA requer ao menos 2 features."]})
        result = pd.DataFrame(PCA(n_components=2).fit_transform(df[features]), columns=["PC1", "PC2"])
        result[target] = df[target].values
        return result


class RandomSamplingStrategy(ReductionStrategy):
    name = "amostragem_aleatoria"

    def reduce(self, df, features, params):
        n = params.get("random_records")
        if not n:
            raise ValidationError("Dados inválidos!", {"random_records": ["O campo é obrigatório."]})
        if n > len(df):
            raise ValidationError("Dados inválidos!", {"random_records": ["Amostra maior que o número de registros."]})
        return df.sample(n=n, replace=False)


class SystematicSamplingStrategy(ReductionStrategy):
    name = "amostragem_sistematica"

    def reduce(self, df, features, params):
        n = params.get("systematic_records")
        method = params.get("systematic_method")
        if not n:
            raise ValidationError("Dados inválidos!", {"systematic_records": ["O campo é obrigatório."]})
        if len(features) != 1:
            raise ValidationError("Dados inválidos!", {"features": ["Apenas uma feature deve ser selecionada."]})
        if method not in ("maiores", "menores"):
            raise ValidationError("Dados inválidos!", {"systematic_method": ["Escolha entre 'maiores' ou 'menores'."]})
        feature = features[0]
        return df.nlargest(n, feature) if method == "maiores" else df.nsmallest(n, feature)


_REGISTRY = {s.name: s for s in (PCAStrategy, RandomSamplingStrategy, SystematicSamplingStrategy)}


def get_strategy(name: str) -> ReductionStrategy:
    strategy = _REGISTRY.get(name)
    if strategy is None:
        raise ValidationError("Dados inválidos!", {"methods": [f"Método inválido: {name}."]})
    return strategy()
