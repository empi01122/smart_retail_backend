from sqlalchemy import create_engine # creates the connection to the database
from sqlalchemy.ext.declarative import declarative_base # base class for all models
from sqlalchemy.orm import sessionmaker # factory that creates DB sessions
from dotenv import load_dotenv # reads variables from the .env file
import os # lets us read environment variables

load_dotenv() # load the .env file so DATABASE_URL is available

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./retail.db") # read DB url, fallback to sqlite

engine = create_engine (   # create the database engine (the actual connection)
    DATABASE_URL,
    pool_pre_ping=True, # Neon DB drops idle connections; this checks if a connection is alive before using it
    pool_recycle=300, # Recycles connections after 5 minutes to avoid unexpected closed connection errors
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # session factory, no auto-saving

Base = declarative_base()
   # all models will inherit from this
   
def get_db():  #this function gives routes a fress DB session
    db = SessionLocal()   # open a new session
    try:
        yield db  # hand the session to the route
    finally:
        db.close()  # always close the session when done