"""
Footprint Updater - Manually update weekly footprint records
This ensures weekly footprint data is created/updated when scans are added
"""

import logging
from datetime import datetime, date, timedelta
from sqlalchemy import func
from models import db, PlasticFootprintScan, UserPlasticFootprintMonthly, User

def get_week_start(date_obj):
    """Get the Monday of the week for a given date"""
    days_since_monday = date_obj.weekday()  # Monday is 0
    return date_obj - timedelta(days=days_since_monday)

def update_weekly_footprint(user_id: int, weight_grams: float):
    """
    Update or create weekly footprint record for a user
    
    Args:
        user_id: User ID
        weight_grams: Weight in grams to add
    """
    try:
        # Get current week start (Monday)
        today = date.today()
        current_week_start = get_week_start(today)
        
        # Get or create weekly record (using month field to store week start)
        weekly = UserPlasticFootprintMonthly.query.filter_by(
            user_id=user_id,
            month=current_week_start
        ).first()
        
        if weekly:
            # Update existing record
            weekly.total_weight_grams = float(weekly.total_weight_grams) + weight_grams
        else:
            # Create new record
            weekly = UserPlasticFootprintMonthly(
                user_id=user_id,
                month=current_week_start,  # Using month field to store week start
                total_weight_grams=weight_grams
            )
            db.session.add(weekly)
        
        # Calculate comparison percentage (vs previous week)
        prev_week_start = current_week_start - timedelta(days=7)
        prev_weekly = UserPlasticFootprintMonthly.query.filter_by(
            user_id=user_id,
            month=prev_week_start
        ).first()
        
        if prev_weekly and float(prev_weekly.total_weight_grams) > 0:
            prev_weight = float(prev_weekly.total_weight_grams)
            current_weight = float(weekly.total_weight_grams)
            comparison_pct = ((current_weight - prev_weight) / prev_weight) * 100.0
        else:
            comparison_pct = 100.0  # First week or no previous data
        
        weekly.comparison_percentage = comparison_pct
        
        # Calculate badge level based on total lifetime weight
        total_lifetime = db.session.query(
            func.sum(UserPlasticFootprintMonthly.total_weight_grams)
        ).filter_by(user_id=user_id).scalar() or 0.0
        
        total_lifetime = float(total_lifetime)
        
        # Badge thresholds (in grams)
        if total_lifetime >= 10000:
            new_badge = 'Champion'
        elif total_lifetime >= 5000:
            new_badge = 'Gold'
        elif total_lifetime >= 2000:
            new_badge = 'Silver'
        else:
            new_badge = 'Bronze'
        
        weekly.badge_level = new_badge
        
        # Update user's badge level
        user = User.query.get(user_id)
        if user:
            user.badge_level = new_badge
        
        db.session.commit()
        logging.info(f"Updated weekly footprint for user {user_id}: {weight_grams}g added, total: {weekly.total_weight_grams}g")
        return True
        
    except Exception as e:
        logging.error(f"Error updating weekly footprint: {e}")
        db.session.rollback()
        return False

# Keep old function name for backward compatibility
def update_monthly_footprint(user_id: int, weight_grams: float):
    """Alias for update_weekly_footprint for backward compatibility"""
    return update_weekly_footprint(user_id, weight_grams)

def sync_all_scans_to_weekly():
    """
    Sync all existing scans to weekly records
    Useful for initial setup or fixing missing data
    """
    try:
        # Get all scans and group by user and week manually
        all_scans = PlasticFootprintScan.query.all()
        
        # Group by user and week (week starts on Monday)
        user_week_data = {}
        for scan in all_scans:
            user_id = scan.user_id
            scan_date = scan.timestamp.date() if scan.timestamp else date.today()
            week_start = get_week_start(scan_date)
            
            key = (user_id, week_start)
            if key not in user_week_data:
                user_week_data[key] = 0.0
            
            user_week_data[key] += float(scan.estimated_weight_grams)
        
        updated_count = 0
        for (user_id, week_start), total_weight in user_week_data.items():
            
            # Get or create weekly record (using month field to store week start)
            weekly = UserPlasticFootprintMonthly.query.filter_by(
                user_id=user_id,
                month=week_start
            ).first()
            
            if weekly:
                weekly.total_weight_grams = total_weight
            else:
                weekly = UserPlasticFootprintMonthly(
                    user_id=user_id,
                    month=week_start,  # Using month field to store week start
                    total_weight_grams=total_weight
                )
                db.session.add(weekly)
            
            # Calculate comparison percentage
            prev_week_start = week_start - timedelta(days=7)
            prev_weekly = UserPlasticFootprintMonthly.query.filter_by(
                user_id=user_id,
                month=prev_week_start
            ).first()
            
            if prev_weekly and float(prev_weekly.total_weight_grams) > 0:
                prev_weight = float(prev_weekly.total_weight_grams)
                current_weight = float(weekly.total_weight_grams)
                comparison_pct = ((current_weight - prev_weight) / prev_weight) * 100.0
            else:
                comparison_pct = 100.0  # First week or no previous data
            
            weekly.comparison_percentage = comparison_pct
            
            # Calculate badge
            total_lifetime = db.session.query(
                func.sum(UserPlasticFootprintMonthly.total_weight_grams)
            ).filter_by(user_id=user_id).scalar() or 0.0
            
            total_lifetime = float(total_lifetime)
            
            if total_lifetime >= 10000:
                new_badge = 'Champion'
            elif total_lifetime >= 5000:
                new_badge = 'Gold'
            elif total_lifetime >= 2000:
                new_badge = 'Silver'
            else:
                new_badge = 'Bronze'
            
            weekly.badge_level = new_badge
            
            # Update user badge
            user = User.query.get(user_id)
            if user:
                user.badge_level = new_badge
            
            updated_count += 1
        
        db.session.commit()
        logging.info(f"Synced {updated_count} weekly footprint records from scans")
        return updated_count
        
    except Exception as e:
        logging.error(f"Error syncing scans to weekly: {e}")
        db.session.rollback()
        return 0

# Keep old function name for backward compatibility
def sync_all_scans_to_monthly():
    """Alias for sync_all_scans_to_weekly for backward compatibility"""
    return sync_all_scans_to_weekly()

