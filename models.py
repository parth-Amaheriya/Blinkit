from pydantic import BaseModel, field_validator
import json
import re


class PriceItem(BaseModel):
    weight: str | None
    original: float | None
    discounted: float | None
    is_selected: bool = False
    
    @field_validator('original', 'discounted', mode='before')
    def convert_currency_to_float(cls, v):
        if v=='Out of stock':
            return None
        if isinstance(v, str):
            v = v.replace("₹", "").replace(",", "").strip()
            return float(v)
        return float(v)


class Media(BaseModel):
    image: list[str]
    video: list[str] 
    


class Product(BaseModel):
    
    product_name: str
    brand: str
    price: list[PriceItem] 
    media: Media
    product_details: dict
