from abc import ABC, abstractmethod

import pandas as pd

from app.common.errors import ValidationError


class MissingValueStrategy(ABC):
    name: str

    @abstractmethod
    def apply(self, series: pd.Series) -> pd.Series: ...


class MeanFillStrategy(MissingValueStrategy):
    name = "media"

    def apply(self, series: pd.Series) -> pd.Series:
        return series.fillna(series.mean().round(4))


class MedianFillStrategy(MissingValueStrategy):
    name = "mediana"

    def apply(self, series: pd.Series) -> pd.Series:
        return series.fillna(series.median().round(4))


class ModeFillStrategy(MissingValueStrategy):
    name = "moda"

    def apply(self, series: pd.Series) -> pd.Series:
        mode = series.mode()
        if mode.empty:
            raise ValidationError(
                "Dados inválidos!",
                {"methods": ["Coluna sem valores válidos para calcular a moda."]},
            )
        return series.fillna(mode.iloc[0])


_REGISTRY = {s.name: s for s in (MeanFillStrategy, MedianFillStrategy, ModeFillStrategy)}


def get_strategy(name: str) -> MissingValueStrategy:
    strategy = _REGISTRY.get(name)
    if strategy is None:
        raise ValidationError("Dados inválidos!", {"methods": [f"Opção inválida: {name}."]})
    return strategy()
