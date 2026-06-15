from fastapi import APIRouter, Depends, HTTPException, status # APIRouter groups routes, Depends injects DB, HTTPException sends errors
from sqlalchemy.orm import Session # type hint for DB session
from typing import List, Optional # for returning lists

from app.database import get_db # function that provides a DB session
from app.auth import get_current_user, get_admin_user # auth dependencies
from models.user import User # User model
from models.product import Product # the Product DB model
from schemas.product import ProductCreate, ProductUpdate, ProductOut # input/output shapes

router = APIRouter(prefix="/products", tags=["Products"]) # all routes here start with /products

def get_product_manager_user(current_user: User = Depends(get_current_user)):
    """
    Checks if the user has catalog management access.
    Proprietors, technicians, and employees (cashiers) can pass this check.
    """
    if current_user.role not in ["technician", "proprietor", "admin", "owner", "employee"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Product management privileges required."
        )
    return current_user

@router.get("/public", response_model=List[ProductOut])
def get_public_products(
    enterprise_id: int,
    db: Session = Depends(get_db)
):
    """
    Public route: Returns all products in catalog for a specific enterprise_id.
    No login required.
    """
    return db.query(Product).filter(Product.enterprise_id == enterprise_id).all()

@router.get("/", response_model=List[ProductOut]) # GET /products -> return all products
def get_all_products(
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):  # DB session + auth injected
    if current_user.role == "technician":
        if enterprise_id is not None:
            return db.query(Product).filter(Product.enterprise_id == enterprise_id).all()
        return db.query(Product).all()
    else:
        # Regular proprietors and employees only see their enterprise's products
        return db.query(Product).filter(Product.enterprise_id == current_user.enterprise_id).all()

@router.get("/{product_id}", response_model=ProductOut) # GET /product -> return one product
def get_product(
    product_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
): # product_id from the URL
    product = db.query(Product).filter(Product.id == product_id).first() # find product by ID
    if not product: # if not found
        raise HTTPException(status_code=404, detail="Product not found")  # return 404 error
        
    # Check permissions
    if current_user.role != "technician" and product.enterprise_id != current_user.enterprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Product belongs to another enterprise."
        )
    return product # return the found product

@router.post("/", response_model=ProductOut, status_code=201) # POST /products -> create new product (admin only)
def create_product(
    product: ProductCreate, 
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    admin: User = Depends(get_product_manager_user)
): # receive product data + admin auth
    target_ent_id = product.enterprise_id or enterprise_id
    if admin.role != "technician":
        target_ent_id = admin.enterprise_id
    elif target_ent_id is None:
        raise HTTPException(
            status_code=400,
            detail="Technicians must specify an enterprise_id when registering products."
        )

    new_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category=product.category,
        image_url=product.image_url,
        enterprise_id=target_ent_id
    )
    db.add(new_product) # stage the new product
    db.commit() # save to database
    db.refresh(new_product) # reload to get generated fields like id and created_at
    return new_product # return the saved product

@router.put("/{product_id}", response_model=ProductOut) # PUT /product/1 -> update a product (admin only)
def update_product(
    product_id: int, 
    updates: ProductUpdate, 
    db: Session = Depends(get_db), 
    admin: User = Depends(get_product_manager_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()  # find the product
    if not product: # if not found
        raise HTTPException(status_code=404, detail="Product not found") # return 404
        
    if admin.role != "technician" and product.enterprise_id != admin.enterprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Product belongs to another enterprise."
        )
    
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items(): # loop only through fields user actually sent
        if field == "enterprise_id" and admin.role != "technician":
            continue # Only technician can move products between enterprises
        setattr(product, field, value) # update each field dynamically
        
    db.commit() # save changes
    db.refresh(product) # reload updated product
    return product # return updated product

@router.delete("/{product_id}", status_code=204) # DELETE /product/1 -> delete a product (admin only)
def delete_product(
    product_id: int, 
    db: Session = Depends(get_db), 
    admin: User = Depends(get_product_manager_user)
):
    product = db.query(Product).filter(Product.id == product_id).first() # find the product
    if not product: # if not found
        raise HTTPException(status_code=404, detail="Product not found") # return 404
        
    if admin.role != "technician" and product.enterprise_id != admin.enterprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Product belongs to another enterprise."
        )
        
    db.delete(product) # mark for deletion
    db.commit()  # permanently delete from database
    return