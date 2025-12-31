"""Check database initialization status"""
from app import app, db
from models import User
from sqlalchemy import inspect

print("Checking database initialization...")
print()

with app.app_context():
    try:
        # Check database connection
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"[OK] Database connected")
        print(f"[OK] Found {len(tables)} tables")
        print(f"  Tables: {', '.join(tables)}")
        print()
        
        # Check if User table exists
        tables_lower = [t.lower() for t in tables]
        if 'user' in tables_lower:
            print("[OK] User table exists")
            
            # Try to query the User table
            try:
                user_count = User.query.count()
                print(f"[OK] User table is accessible - {user_count} users found")
                
                # Try a simple query
                test_user = User.query.first()
                if test_user:
                    print(f"[OK] User query test passed - found user: {test_user.username}")
                else:
                    print("[OK] User query test passed - no users yet (this is normal)")
                    
            except Exception as e:
                print(f"[ERROR] Cannot query User table: {e}")
                print("  This is why registration is failing!")
                import traceback
                traceback.print_exc()
        else:
            print("[ERROR] User table does not exist!")
            print("  Initializing database tables...")
            db.create_all()
            print("[OK] Database tables created")
            
    except Exception as e:
        print(f"[ERROR] Database check failed: {e}")
        import traceback
        traceback.print_exc()

