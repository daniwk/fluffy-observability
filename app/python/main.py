from typing import Union
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/hello")
def read_root():
    r = requests.get('https://api.github.com/user')
    r.status_code
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
