from fastapi import APIRouter, Depends # APIRouter groups. Depends injects dependencies
from sqlalchemy.orm import Session # type hint for the DB session
from typing import List # for returning a list of sales

from app.database import get_db # function that gives us a DB session
from models.sale import Sale # the Sale database model
from schemas.sale import SaleCreate, SaleOut # input and output shapes
from services.business_logic import create_sale_with_stock_update, create_sale_with_stock_update # core logic

router = APIRouter(prefix="/sales", tags=["Sales"]) # all routes here start with /sales

@router.get("/", response_model=List[SaleOut]) # Get /sales -> return all sales
def get_all_sales(db: Session = Depends(get_db)): # db is injected automatically
    return db.query(Sale).order_by(Sale.created_at.desc()).all() # newest sales first

@router.post("/",response_model=SaleOut, status_code=201) # POST /sales -> record a new sale
def record_sale(sale_data: SaleCreate, db: Session = Depends(get_db)): # reveive sale data + db
    return create_sale_with_stock_update(db, sale_data) # hand off to business logic
