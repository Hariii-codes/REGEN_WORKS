"""
Migration script for new ReGenWorks features
Works with both SQLite and PostgreSQL
"""

import os
import sys
import logging
from app import app, db
from sqlalchemy import text, inspect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def table_exists(conn, table_name):
    """Check if a table exists"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def add_column_sqlite(conn, table_name, column_name, column_type, default_value=None):
    """Add column to SQLite table (SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS)"""
    try:
        # SQLite doesn't support IF NOT EXISTS for ALTER TABLE
        # So we check first and then add
        if not column_exists(conn, table_name, column_name):
            default_clause = f" DEFAULT {default_value}" if default_value is not None else ""
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_clause}"
            conn.execute(text(sql))
            # Don't commit here - let the context manager handle it
            logger.info(f"[OK] Added column '{column_name}' to table '{table_name}'")
            return True
        else:
            logger.info(f"[SKIP] Column '{column_name}' already exists in table '{table_name}'")
            return False
    except Exception as e:
        logger.error(f"[ERROR] Error adding column '{column_name}' to '{table_name}': {e}")
        return False

def add_column_postgres(conn, table_name, column_name, column_type, default_value=None):
    """Add column to PostgreSQL table"""
    try:
        default_clause = f" DEFAULT {default_value}" if default_value is not None else ""
        sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}{default_clause}"
        conn.execute(text(sql))
        # Don't commit here - let the context manager handle it
        logger.info(f"[OK] Added column '{column_name}' to table '{table_name}'")
        return True
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            logger.info(f"[SKIP] Column '{column_name}' already exists in table '{table_name}'")
            return False
        logger.error(f"[ERROR] Error adding column '{column_name}' to '{table_name}': {e}")
        return False

def is_sqlite():
    """Check if database is SQLite"""
    return db.engine.url.drivername == 'sqlite'

def migrate_user_table():
    """Add new columns to user table"""
    logger.info("Migrating user table...")
    
    with db.engine.begin() as conn:
        if is_sqlite():
            add_column_sqlite(conn, 'user', 'preferred_language', 'VARCHAR(10)', "'en'")
            add_column_sqlite(conn, 'user', 'voice_input_enabled', 'BOOLEAN', '1')
            add_column_sqlite(conn, 'user', 'onboarding_completed', 'BOOLEAN', '0')
            add_column_sqlite(conn, 'user', 'badge_level', 'VARCHAR(20)', "'Bronze'")
        else:
            add_column_postgres(conn, 'user', 'preferred_language', 'VARCHAR(10)', "'en'")
            add_column_postgres(conn, 'user', 'voice_input_enabled', 'BOOLEAN', 'TRUE')
            add_column_postgres(conn, 'user', 'onboarding_completed', 'BOOLEAN', 'FALSE')
            add_column_postgres(conn, 'user', 'badge_level', 'VARCHAR(20)', "'Bronze'")

def migrate_waste_item_table():
    """Add new columns to waste_item table"""
    logger.info("Migrating waste_item table...")
    
    with db.engine.begin() as conn:
        if is_sqlite():
            add_column_sqlite(conn, 'waste_item', 'material_type', 'VARCHAR(50)', 'NULL')
            add_column_sqlite(conn, 'waste_item', 'estimated_weight_grams', 'REAL', 'NULL')
            add_column_sqlite(conn, 'waste_item', 'ml_confidence_score', 'REAL', 'NULL')
        else:
            add_column_postgres(conn, 'waste_item', 'material_type', 'VARCHAR(50)', 'NULL')
            add_column_postgres(conn, 'waste_item', 'estimated_weight_grams', 'NUMERIC(10,2)', 'NULL')
            add_column_postgres(conn, 'waste_item', 'ml_confidence_score', 'NUMERIC(5,2)', 'NULL')

def create_new_tables():
    """Create all new tables for the features"""
    logger.info("Creating new tables...")
    
    try:
        # Import all models to ensure they're registered
        from models import (
            UserPlasticFootprintMonthly,
            PlasticFootprintScan,
            MaterialWeightLookup,
            LocalizationString,
            InfrastructureProject,
            WasteBatch,
            ProjectContributor,
            ProjectLedger
        )
        
        # Create all tables
        db.create_all()
        logger.info("[OK] All new tables created successfully")
        
        # Seed initial data
        seed_initial_data()
        
    except Exception as e:
        logger.error(f"[ERROR] Error creating tables: {e}")
        raise

def seed_initial_data():
    """Seed initial data for lookup tables"""
    logger.info("Seeding initial data...")
    
    try:
        from models import MaterialWeightLookup, LocalizationString
        
        # Check if data already exists
        existing_count = MaterialWeightLookup.query.count()
        if existing_count == 0:
            logger.info("Seeding material_weight_lookup...")
            weight_data = [
                MaterialWeightLookup(
                    material_type='Plastic',
                    category='plastic_bottle',
                    average_weight_grams=25.0,
                    min_weight_grams=15.0,
                    max_weight_grams=50.0,
                    confidence_threshold=0.70
                ),
                MaterialWeightLookup(
                    material_type='Plastic',
                    category='plastic_bag',
                    average_weight_grams=5.0,
                    min_weight_grams=2.0,
                    max_weight_grams=10.0,
                    confidence_threshold=0.65
                ),
                MaterialWeightLookup(
                    material_type='Plastic',
                    category='plastic_container',
                    average_weight_grams=30.0,
                    min_weight_grams=20.0,
                    max_weight_grams=100.0,
                    confidence_threshold=0.75
                ),
                MaterialWeightLookup(
                    material_type='Paper',
                    category='paper_sheet',
                    average_weight_grams=5.0,
                    min_weight_grams=2.0,
                    max_weight_grams=10.0,
                    confidence_threshold=0.70
                ),
                MaterialWeightLookup(
                    material_type='Paper',
                    category='cardboard_box',
                    average_weight_grams=200.0,
                    min_weight_grams=100.0,
                    max_weight_grams=500.0,
                    confidence_threshold=0.75
                ),
                MaterialWeightLookup(
                    material_type='Metal',
                    category='aluminum_can',
                    average_weight_grams=15.0,
                    min_weight_grams=10.0,
                    max_weight_grams=25.0,
                    confidence_threshold=0.70
                ),
                MaterialWeightLookup(
                    material_type='Metal',
                    category='steel_can',
                    average_weight_grams=50.0,
                    min_weight_grams=30.0,
                    max_weight_grams=100.0,
                    confidence_threshold=0.75
                ),
                MaterialWeightLookup(
                    material_type='Glass',
                    category='glass_bottle',
                    average_weight_grams=300.0,
                    min_weight_grams=200.0,
                    max_weight_grams=500.0,
                    confidence_threshold=0.75
                ),
                MaterialWeightLookup(
                    material_type='Glass',
                    category='glass_container',
                    average_weight_grams=150.0,
                    min_weight_grams=100.0,
                    max_weight_grams=300.0,
                    confidence_threshold=0.70
                ),
            ]
            
            for item in weight_data:
                db.session.add(item)
            db.session.commit()
            logger.info(f"[OK] Material weight lookup data seeded ({len(weight_data)} items)")
        else:
            logger.info(f"[SKIP] Material weight lookup data already exists ({existing_count} items)")
        
        # Seed localization strings (sample - add more as needed)
        if LocalizationString.query.first() is None:
            logger.info("Seeding localization_strings...")
            localization_data = [
                # Navigation
                LocalizationString(key='nav.scan', language='en', value='Scan Waste', context='both'),
                LocalizationString(key='nav.scan', language='hi', value='कचरा स्कैन करें', context='both'),
                LocalizationString(key='nav.scan', language='kn', value='ಕಸ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ', context='both'),
                LocalizationString(key='nav.scan', language='ta', value='கழிவு ஸ்கேன் செய்யவும்', context='both'),
                LocalizationString(key='nav.scan', language='mr', value='कचरा स्कॅन करा', context='both'),
                
                LocalizationString(key='nav.drop_points', language='en', value='Drop Points', context='both'),
                LocalizationString(key='nav.drop_points', language='hi', value='ड्रॉप पॉइंट्स', context='both'),
                LocalizationString(key='nav.drop_points', language='kn', value='ಡ್ರಾಪ್ ಪಾಯಿಂಟ್ಗಳು', context='both'),
                LocalizationString(key='nav.drop_points', language='ta', value='டிராப் புள்ளிகள்', context='both'),
                LocalizationString(key='nav.drop_points', language='mr', value='ड्रॉप पॉइंट्स', context='both'),
                
                LocalizationString(key='nav.dashboard', language='en', value='Dashboard', context='both'),
                LocalizationString(key='nav.dashboard', language='hi', value='डैशबोर्ड', context='both'),
                LocalizationString(key='nav.dashboard', language='kn', value='ಡ್ಯಾಶ್ಬೋರ್ಡ್', context='both'),
                LocalizationString(key='nav.dashboard', language='ta', value='டாஷ்போர்டு', context='both'),
                LocalizationString(key='nav.dashboard', language='mr', value='डॅशबोर्ड', context='both'),
                
                LocalizationString(key='nav.rewards', language='en', value='Rewards', context='both'),
                LocalizationString(key='nav.rewards', language='hi', value='इनाम', context='both'),
                LocalizationString(key='nav.rewards', language='kn', value='ಬಹುಮಾನಗಳು', context='both'),
                LocalizationString(key='nav.rewards', language='ta', value='வெகுமதிகள்', context='both'),
                LocalizationString(key='nav.rewards', language='mr', value='बक्षीस', context='both'),
                
                # Actions
                LocalizationString(key='action.scan', language='en', value='Scan', context='both'),
                LocalizationString(key='action.scan', language='hi', value='स्कैन', context='both'),
                LocalizationString(key='action.scan', language='kn', value='ಸ್ಕ್ಯಾನ್', context='both'),
                LocalizationString(key='action.scan', language='ta', value='ஸ்கேன்', context='both'),
                LocalizationString(key='action.scan', language='mr', value='स्कॅन', context='both'),
                
                LocalizationString(key='action.submit', language='en', value='Submit', context='both'),
                LocalizationString(key='action.submit', language='hi', value='सबमिट करें', context='both'),
                LocalizationString(key='action.submit', language='kn', value='ಸಲ್ಲಿಸಿ', context='both'),
                LocalizationString(key='action.submit', language='ta', value='சமர்ப்பிக்கவும்', context='both'),
                LocalizationString(key='action.submit', language='mr', value='सबमिट करा', context='both'),
            ]
            
            for item in localization_data:
                db.session.add(item)
            db.session.commit()
            logger.info("[OK] Localization strings seeded")
        else:
            logger.info("[SKIP] Localization strings already exist")
            
    except Exception as e:
        logger.error(f"[ERROR] Error seeding data: {e}")
        db.session.rollback()
        raise

def main():
    """Run all migrations"""
    logger.info("Starting ReGenWorks feature migration...")
    
    try:
        with app.app_context():
            logger.info(f"Database: {db.engine.url.drivername}")
            
            # Step 1: Migrate existing tables
            migrate_user_table()
            migrate_waste_item_table()
            
            # Step 2: Create new tables
            create_new_tables()
            
            logger.info("Migration completed successfully!")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

