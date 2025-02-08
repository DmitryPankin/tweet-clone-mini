from fastapi import FastAPI

import os

from .routers.tweets import router

def get_dist_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "../dist")
    return dist_dir


app = FastAPI()

app.include_router(router)




