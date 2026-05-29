from pydantic import BaseModel, ConfigDict


class UserReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone_number: str
    email: str
