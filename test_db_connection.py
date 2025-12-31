"""Test PostgreSQL database connection"""
import os
import sys

# Use DATABASE_URL from environment or .env file
# If not set, it will use the default from app.py

try:
    from app import app, db
    from sqlalchemy import inspect
    
    print("Testing PostgreSQL connection...")
    print(f"Database URL: postgresql://postgres:***@localhost:5432/waste_management")
    print()
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("[OK] Connected to PostgreSQL database: waste_management")
            print(f"[OK] Found {len(tables)} tables")
            
            if tables:
                print(f"  Tables: {', '.join(tables[:10])}")
                if len(tables) > 10:
                    print(f"  ... and {len(tables) - 10} more")
            else:
                print("  No tables found - need to initialize database")
                print()
                print("To initialize database, run:")
                print("  python recreate_db.py")
            
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            print()
            print("Please check:")
            print("  1. PostgreSQL is running")
            print("  2. Database 'waste_management' exists")
            print("  3. Username and password are correct")
            print("  4. PostgreSQL is listening on port 5432")
            sys.exit(1)
            
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error: {e}")
    sys.exit(1)

