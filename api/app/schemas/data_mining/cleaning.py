from pydantic import BaseModel, Field


class DataCleaningSchema(BaseModel):
    features: list[str] = Field(min_length=1)
    methods: str
    missing_values: list[str] = Field(min_length=1, max_length=4)
