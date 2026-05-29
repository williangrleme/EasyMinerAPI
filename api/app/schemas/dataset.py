from pydantic import BaseModel, ConfigDict, Field


class DatasetCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    project_id: int


class DatasetUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    project_id: int | None = None


class CleanDatasetReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    size_file: str
    file_url: str


class DatasetReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    size_file: str
    file_url: str | None
    project_id: int
    clean_dataset: CleanDatasetReadSchema | None = None
