"""
Create Pickup Service Tables in Database
Run this script to create the new pickup tables without affecting existing data
"""

from app import app, db

def create_pickup_tables():
    """Create pickup service tables"""
    print("=" * 60)
    print("ReGenWorks - Creating Pickup Service Tables")
    print("=" * 60)
    print()

    with app.app_context():
        from models import PickupPartner, PickupRequest, PickupTimeSlot

        # Create all new tables
        print("Creating new pickup tables...")
        db.create_all()
        print("✓ Tables created successfully!")

        print()
        print("=" * 60)
        print("✓ Pickup service tables are ready!")
        print("=" * 60)
        print()
        print("Now run 'python init_pickup_data.py' to populate sample data")
        print()

if __name__ == '__main__':
    create_pickup_tables()
