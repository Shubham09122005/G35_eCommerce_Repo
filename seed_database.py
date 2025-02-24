import random
from app import db, app  # Import Flask app & dSmartwatchatabase
from app import Product  # Import Product model

# Categories
categories = ["electronics", "fashion", "home-living", "sports-outdoors", "beauty"]

# Sample product names for each category
sample_products = {
    "electronics": ["Laptop", "Smartphone", "Headphones", "Smartwatch", "Tablet", "Monitor", "Camera", "Printer", "Speakers", "Gaming Mouse",
                     "Keyboard", "Router", "Power Bank", "VR Headset", "External Hard Drive", "Drone", "Microphone", "Graphics Card", "Smart TV", "Projector"],
    "fashion": ["T-shirt", "Jeans", "Sneakers", "Jacket", "Dress", "Wristwatch", "Handbag", "Sunglasses", "Hat", "Belt",
                 "Scarf", "Earrings", "Necklace", "Sweater", "Socks", "Formal Shoes", "Shorts", "Blazer", "Perfume", "Backpack"],
    "home-living": ["Sofa", "Dining Table", "Chair", "Lamp", "Curtains", "Bedsheet", "Pillow", "Wall Clock", "Bookshelf", "Storage Box",
                     "Carpet", "Coffee Table", "Vase", "Dinner Set", "Pressure Cooker", "Fan", "Mirror", "Wardrobe", "Mattress", "Laundry Basket"],
    "sports-outdoors": ["Football", "Basketball", "Tennis Racket", "Cricket Bat", "Dumbbells", "Yoga Mat", "Running Shoes", "Cycling Helmet", "Treadmill", "Hiking Backpack",
                        "Swimming Goggles", "Jump Rope", "Boxing Gloves", "Badminton Racket", "Skateboard", "Golf Clubs", "Fishing Rod", "Camping Tent", "Dart Board", "Archery Set"],
    "beauty": ["Lipstick", "Foundation", "Mascara", "Eyeliner", "Face Cream", "Perfume", "Hair Dryer", "Nail Polish", "Serum", "Face Wash",
                "Sunscreen", "Shampoo", "Conditioner", "Body Lotion", "Hair Oil", "Face Mask", "Makeup Kit", "Toner", "Blush", "Compact Powder"]
}

def seed_database(overwrite=True):
    with app.app_context():
        if overwrite:
            db.session.query(Product).delete()  # Delete all existing records
            db.session.commit()
            print("⚠️ Existing database records deleted!")

        products = []
        for category in categories:
            for product_name in sample_products[category]:
                product = Product(
                    name=product_name,
                    image_url=f"{product_name}.jpg",  # Placeholder image
                    price=round(random.uniform(2000, 50000), 2),  # Random price between $10 and $500
                    stock=random.randint(1, 50),  # Random stock between 1 and 50
                    category=category
                )
                products.append(product)
        
        db.session.bulk_save_objects(products)  # Fast insertion
        db.session.commit()
        print("✅ 100 products have been seeded into the database!")

if __name__ == "__main__":
    overwrite = input("Do you want to overwrite the existing database? (yes/no): ").strip().lower() == "yes"
    seed_database(overwrite)
