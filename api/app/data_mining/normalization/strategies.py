from abc import ABC, abstractmethod

import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from app.common.errors import ValidationError


class NormalizationStrategy(ABC):
    name: str

    def apply(self, series: pd.Series) -> pd.Series:
        scaled = self._scaler().fit_transform(series.values.reshape(-1, 1))
        return pd.Series(scaled.flatten(), index=series.index).round(4)

    @abstractmethod
    def _scaler(self): ...


class MinMaxStrategy(NormalizationStrategy):
    name = "minmax"

    def _scaler(self):
        return MinMaxScaler()


class ZScoreStrategy(NormalizationStrategy):
    name = "zscore"

    def _scaler(self):
        return StandardScaler()


_REGISTRY = {s.name: s for s in (MinMaxStrategy, ZScoreStrategy)}


def get_strategy(name: str) -> NormalizationStrategy:
    strategy = _REGISTRY.get(name)
    if strategy is None:
        raise ValidationError("Dados inválidos!", {"methods": [f"Método inválido: {name}."]})
    return strategy()
