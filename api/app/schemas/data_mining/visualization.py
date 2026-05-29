from pydantic import BaseModel, Field


class VisualizationSchema(BaseModel):
    features: list[str] = Field(min_length=1)
    visualization_method: str
    use_clean_dataset: bool = False
