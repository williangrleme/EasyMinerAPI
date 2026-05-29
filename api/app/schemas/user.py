from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone_number: str
    email: str


class UserCreateSchema(BaseModel):
    name: str = Field(min_length=10, max_length=150)
    phone_number: str = Field(min_length=11, max_length=20)
    email: EmailStr = Field(max_length=200)
    password: str = Field(min_length=8, max_length=30)


class UserUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=10, max_length=150)
    phone_number: str | None = Field(default=None, min_length=11, max_length=20)
    email: EmailStr | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, min_length=8, max_length=30)
