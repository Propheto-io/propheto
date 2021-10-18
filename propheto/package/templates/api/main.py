from fastapi import FastAPI
from v1.routers import router
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Propheto API",
    description="Sample API for the Propheto ML model service",
    root_path="/dev",
    version="0.1.0",
)
app.include_router(router, prefix="/v1")

origins = [
    "http://app.getpropheto.com",
    "https://app.getpropheto.com",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello ML Practitioner": "from the Propheto ML service"}


@app.get("/status")
def read_root():
    return {"message": "Active"}


@app.get("/ping")
def read_root():
    return {"message": "pong"}


# to make it work with Amazon Lambda, we create a handler object
handler = Mangum(app=app)
