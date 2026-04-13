from fastapi import FastAPI # FastAPI is the main framework class
from fastapi.middleware.cors import CORSMiddleware # allows React frontend to talk to this API
from dotenv import load_dotenv # reads variables from the .env file
import os # lets us read environment variables

from app.database import engine, Base # engine = DB connection, Base = parent of all models
from routes import product, sales, dashboard, settings # import all route files

load_dotenv(override=True) # load env file so APP_NAME and DATABASE_URL are available

Base.metadata.create_all(bind=engine) # automaticaly create all DB tables if they don't exist

app = FastAPI ( # create the FastAPI application
    title=os.getenv("APP_NAME", "Smart Retail System"), # app name from .env
    description="API for managing products. sales, stock, and insights", # shows in docs
    version="1.0.0" # API version
)

app.add_middleware(  # add CORS middleware so browser requests are allowed
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # allowed frontend URLs
    allow_credentials=True, # allows cookies and auth headers
    allow_methods=["*"], # allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"], # allow all headers
)

app.include_router(product.router) # register all /products routes
app.include_router(sales.router) # register all /sales routes
app.include_router(dashboard.router) # register all /dashboard routes
app.include_router(settings.router) # register all /settings routes

@app.get("/")  # GET / -> health check, confirms API is running
def root():
    return {"message": "Smart Retail System API is running✅"}   # simple confirmation responses