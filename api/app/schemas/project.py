from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=2000)


class ProjectUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=2000)


class DatasetSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    size_file: str
    file_url: str | None


class ProjectReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None


class ProjectDetailSchema(ProjectReadSchema):
    datasets: list[DatasetSummarySchema] = []
