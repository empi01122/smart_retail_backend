from fastapi import APIRouter, Depends, HTTPException # APIRouter groups routes, Depends injects DB, HTTPException sends errors
from sqlalchemy.orm import Session # type hint for DB session
from typing import List # for returning lists

from app.database import get_db # function that provides a DB session
from app.auth import get_current_user, get_admin_user # auth dependencies
from models.user import User # User model
from models.product import Product # the Product DB model
from schemas.product import ProductCreate, ProductUpdate, ProductOut # input/output shapes

router = APIRouter(prefix="/products", tags=["Products"]) # all routes here start with /products

@router.get("/", response_model=List[ProductOut]) # GET /products -> return all products
def get_all_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):  # DB session + auth injected
    return db.query(Product).all() # fetch and return product

@router.get("/{product_id}", response_model=ProductOut) # GET /product -> return one product
def get_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # product_id from the URL
    product = db.query(Product).filter(Product.id == product_id).first() # find product by ID
    if not product: # if not found
        raise HTTPException(status_code=404, detail="Product not found")  # return 404 error
    return product # return the found product

@router.post("/", response_model=ProductOut, status_code=201) # POST /products -> create new product (admin only)
def create_product(product: ProductCreate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)): # receive product data + admin auth
    new_product = Product(**product.model_dump()) # convert schema to model, unpack all fields
    db.add(new_product) # stage the new product
    db.commit() # save to database
    db.refresh(new_product) # reload to get generated fields like id and created_at
    return new_product # return the saved product

@router.put("/{product_id}", response_model=ProductOut) # PUT /product/1 -> update a product (admin only)
def update_product(product_id: int, updates: ProductUpdate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    product = db.query(Product).filter(Product.id == product_id).first()  # find the product
    if not product: # if not found
        raise HTTPException(status_code=404, detail="Product not found") # return 404
    
    for field, value in updates.model_dump(exclude_unset=True).items(): # loop only through fields user actually sent
        setattr(product, field, value) # update each field dynamically
        
    db.commit() # save changes
    db.refresh(product) # reload updated product
    return product # return updated product

@router.delete("/{product_id}", status_code=204) # DELETE /product/1 -> delete a product (admin only)
def delete_product(product_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    product = db.query(Product).filter(Product.id == product_id).first() # find the product
    if not product: # if not found
        raise HTTPException(status_code=404, detail="Product not found") # return 404
    db.delete(product) # mark for deletion
    db.commit()  # permanently delete from database