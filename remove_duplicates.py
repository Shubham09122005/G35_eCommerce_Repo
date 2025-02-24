from app import db, app  # Import Flask app & database
from app import Product, CartItem  # Import models

def remove_duplicates():
    with app.app_context():  # Establish Flask app context
        unique_products = set()
        duplicates = []

        # Fetch all products
        products = Product.query.all()
        
        for product in products:
            identifier = (product.name, product.category, product.price)
            if identifier in unique_products:
                duplicates.append(product)
            else:
                unique_products.add(identifier)

        # Handle related records before deleting products
        for duplicate in duplicates:
            # Remove references in cart_item before deleting product
            CartItem.query.filter_by(product_id=duplicate.id).delete()
            db.session.delete(duplicate)

        db.session.commit()
        print(f"Removed {len(duplicates)} duplicate products.")

if __name__ == "__main__":
    remove_duplicates()
