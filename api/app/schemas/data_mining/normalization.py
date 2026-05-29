from pydantic import BaseModel, Field


class DataNormalizationSchema(BaseModel):
    features: list[str] = Field(min_length=1)
    methods: str
