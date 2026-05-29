from pydantic import BaseModel, Field


class DataReductionSchema(BaseModel):
    features: list[str] = Field(min_length=1)
    methods: str
    target: str | None = None
    random_records: int | None = None
    systematic_records: int | None = None
    systematic_method: str | None = None
