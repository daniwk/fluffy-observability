from typing import Union
# from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI

app = FastAPI()

# @app.on_event("startup")
# async def startup():
#     Instrumentator().instrument(app).expose(app)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
