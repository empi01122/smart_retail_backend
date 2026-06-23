from fastapi import FastAPI # FastAPI is the main framework class
from fastapi.middleware.cors import CORSMiddleware # allows React frontend to talk to this API
from dotenv import load_dotenv # reads variables from the .env file
import os # lets us read environment variables

from app.database import engine, Base # engine = DB connection, Base = parent of all models
from routes import product, sales, dashboard, settings, users, enterprise # import all route files

# Explicitly import all models to register them in the SQLAlchemy metadata registry before mapping
from models.user import User
from models.enterprise import Enterprise, Review
from models.product import Product
from models.sale import Sale
from models.sale_item import SaleItem
from models.settings import StoreSettings

load_dotenv(override=True) # load env file so APP_NAME and DATABASE_URL are available

Base.metadata.create_all(bind=engine) # automaticaly create all DB tables if they don't exist

app = FastAPI ( # create the FastAPI application
    title=os.getenv("APP_NAME", "Smart Retail System"), # app name from .env
    description="API for managing products. sales, stock, and insights", # shows in docs
    version="1.0.0" # API version
)

frontend_url = os.getenv("FRONTEND_URL")
allowed_origins = [
    "http://localhost:5173", 
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000"
]
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(  # add CORS middleware so browser requests are allowed
    CORSMiddleware,
    allow_origins=allowed_origins, # allowed frontend URLs
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?|https?://.*\.vercel\.app",
    allow_credentials=True, # allows cookies and auth headers
    allow_methods=["*"], # allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"], # allow all headers
)

app.include_router(product.router) # register all /products routes
app.include_router(sales.router) # register all /sales routes
app.include_router(dashboard.router) # register all /dashboard routes
app.include_router(settings.router) # register all /settings routes
app.include_router(users.router) # register all /users routes
app.include_router(enterprise.router) # register all /enterprises routes

@app.api_route("/", methods=["GET", "HEAD"])  # GET / or HEAD / -> health check, confirms API is running
def root():
    return {"message": "Smart Retail System API is running✅"}   # simple confirmation responses

@app.get("/favicon.ico", include_in_schema=False)  # suppress browser favicon 404 noise
def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)  # 204 No Content — tells browser there's no favicon