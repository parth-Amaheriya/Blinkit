from pydantic import BaseModel, field_validator


class PriceItem(BaseModel):
    weight: str |None
    original: float|None
    discounted: float|None
    
    @field_validator('original', 'discounted', mode='before')
    def convert_currency_to_float(cls, v):
        if v=='Out of stock':
            return None
        if isinstance(v, str):
            v = v.replace("₹", "").replace(",","").strip()
            return float(v)
        return float(v)


class Media(BaseModel):
    image: list[str]|None
    video: list[str] |None
    


class Product(BaseModel):
    
    product_name: str|None
    brand: str|None
    price: list[PriceItem]|None
    media: Media|None
    product_details: dict|None