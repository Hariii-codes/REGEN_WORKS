"""Create regenworks database if it doesn't exist and initialize tables"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

try:
    # Connect to PostgreSQL server (using postgres database)
    print("Connecting to PostgreSQL server...")
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='1234',
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Check if regenworks database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname='regenworks'")
    exists = cur.fetchone()
    
    if exists:
        print("[OK] Database 'regenworks' already exists")
    else:
        print("Creating database 'regenworks'...")
        cur.execute('CREATE DATABASE regenworks WITH ENCODING \'UTF8\'')
        print("[OK] Database 'regenworks' created successfully")
    
    cur.close()
    conn.close()
    
    # Now test connection to regenworks database
    print("\nTesting connection to regenworks database...")
    os.environ['DATABASE_URL'] = 'postgresql://postgres:1234@localhost:5432/regenworks'
    
    from app import app, db
    from sqlalchemy import inspect
    
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"[OK] Connected to regenworks database")
        print(f"[OK] Found {len(tables)} tables")
        
        if tables:
            print(f"  Tables: {', '.join(tables[:10])}")
            if len(tables) > 10:
                print(f"  ... and {len(tables) - 10} more")
        else:
            print("  No tables found - initializing database...")
            db.create_all()
            print("[OK] Database tables created")
    
    print("\n[OK] Setup complete! Your application is ready to use the regenworks database.")
    
except psycopg2.OperationalError as e:
    print(f"[ERROR] Could not connect to PostgreSQL: {e}")
    print("\nPlease check:")
    print("  1. PostgreSQL is running")
    print("  2. Username and password are correct")
    print("  3. PostgreSQL is listening on port 5432")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

