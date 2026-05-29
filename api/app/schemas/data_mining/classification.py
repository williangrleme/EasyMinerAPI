from pydantic import BaseModel, Field, model_validator

_VALID_METRICS = {"euclidean", "manhattan", "minkowski", "mahalanobis"}


class ClassificationSchema(BaseModel):
    features: list[str] = Field(min_length=1)
    target: str
    classification_method: str = "knn"
    distance_metric: str = "euclidean"
    k_neighbors: int = Field(default=5, ge=1)
    test_size: float = Field(default=0.3, ge=0.1, le=0.9)
    use_clean_dataset: bool = False

    @model_validator(mode="after")
    def _check(self):
        if self.distance_metric not in _VALID_METRICS:
            raise ValueError(f"Métrica de distância '{self.distance_metric}' não é válida.")
        if self.target in self.features:
            raise ValueError("O campo target não pode estar incluído nas features.")
        return self
