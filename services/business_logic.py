from sqlalchemy.orm import Session
from fastapi import HTTPException
import random

from models.product import Product
from models.sale import Sale
from models.sale_item import SaleItem
from schemas.sale import SaleCreate

def create_sale_with_stock_update(db: Session, sale_data: SaleCreate, enterprise_id: int) -> Sale:
    """
    Handles the full sale process: validation, cross-enterprise checking,
    stock deduction, and escrow payment configuration (if using mobile money).
    """
    total = 0.0
    items_to_create = []
    
    # STEP 1 - validate every item BEFORE touching the database
    for item in sale_data.items:
        # Secure check: product must exist AND belong to the active enterprise
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.enterprise_id == enterprise_id
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with id {item.product_id} not found in this enterprise catalog."
            )
        
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for '{product.name}'. Available: {product.stock}, Requested: {item.quantity}"
            )
            
        subtotal = product.price * item.quantity
        total += subtotal
        items_to_create.append((product, item.quantity, product.price))
            
    # STEP 2 - configure payment status and delivery PIN for escrow
    # Escrow only applies to online delivery orders — not walk-in customers.
    # A walk-in paying MoMo gets their product immediately so no PIN is needed.
    is_escrow = (sale_data.source == "online")
    payment_status = "paid_escrow" if is_escrow else "completed"
    delivery_pin = str(random.randint(1000, 9999)) if is_escrow else None

    from datetime import datetime, timezone

    # Create the Sale record
    sale = Sale(
        total_amount=round(total, 2),
        payment_status=payment_status,
        payment_method=sale_data.payment_method or "cash",
        delivery_pin=delivery_pin,
        enterprise_id=enterprise_id,
        created_at=sale_data.created_at or datetime.now(timezone.utc),
        # Online / delivery fields
        source=sale_data.source or "pos",
        customer_name=sale_data.customer_name,
        customer_phone=sale_data.customer_phone,
        delivery_address=sale_data.delivery_address,
        order_note=sale_data.order_note,
    )
    db.add(sale)
    db.flush() # Generate sale.id
    
    # STEP 3 - create each SaleItem and reduce product stock
    for product, quantity, unit_price in items_to_create:
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=unit_price
        )
        db.add(sale_item)
        product.stock -= quantity
        
    db.commit()
    db.refresh(sale)
    return sale
         