"""Test registration database check"""
from app import app, db
from models import User
from sqlalchemy import inspect

print("Testing registration database check...")
print()

with app.app_context():
    try:
        # This is the same check used in the registration route
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        tables_lower = [t.lower() for t in tables]
        
        print(f"Found {len(tables)} tables")
        print(f"User table exists: {'user' in tables_lower}")
        
        if 'user' in tables_lower:
            print("[OK] Registration should work - User table exists")
            
            # Test creating a user (don't actually create, just test the model)
            try:
                test_user = User(username="test", email="test@test.com")
                test_user.set_password("test123")
                print("[OK] User model works correctly")
            except Exception as e:
                print(f"[ERROR] User model error: {e}")
        else:
            print("[ERROR] Registration will fail - User table does not exist")
            print("  Run: python recreate_db.py")
            
    except Exception as e:
        print(f"[ERROR] Database check failed: {e}")
        import traceback
        traceback.print_exc()

