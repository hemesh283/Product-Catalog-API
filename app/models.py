from pydantic import BaseModel, Field


class Product(BaseModel):
    id: int
    name: str
    description: str
    price_paise: int = Field(ge=0)
    image_url: str