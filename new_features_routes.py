"""
Web routes for new ReGenWorks features:
1. Plastic Footprint Tracker
2. Infrastructure Projects
3. Multilingual Support (language selector)
"""

from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app import db
from models import (
    UserPlasticFootprintMonthly, PlasticFootprintScan, MaterialWeightLookup,
    InfrastructureProject, WasteBatch, ProjectContributor, ProjectLedger,
    LocalizationString
)
from datetime import datetime, date
from sqlalchemy import func, desc
import logging

def register_new_feature_routes(app):
    """Register web routes for new features"""
    
    # ============================================================================
    # PLASTIC FOOTPRINT TRACKER
    # ============================================================================
    
    @app.route('/footprint-dashboard')
    @login_required
    def footprint_dashboard():
        """Display plastic footprint dashboard (weekly-based)"""
        try:
            from footprint_updater import get_week_start
            
            # Get weekly history (last 12 weeks)
            weekly_history = UserPlasticFootprintMonthly.query.filter_by(
                user_id=current_user.id
            ).order_by(desc(UserPlasticFootprintMonthly.month)).limit(12).all()
            
            # Get current week start (Monday)
            today = date.today()
            current_week_start = get_week_start(today)
            current_weekly = UserPlasticFootprintMonthly.query.filter_by(
                user_id=current_user.id,
                month=current_week_start
            ).first()
            
            # Get recent scans
            recent_scans = PlasticFootprintScan.query.filter_by(
                user_id=current_user.id
            ).order_by(desc(PlasticFootprintScan.timestamp)).limit(10).all()
            
            # Calculate total lifetime weight
            total_lifetime = db.session.query(
                func.sum(UserPlasticFootprintMonthly.total_weight_grams)
            ).filter_by(user_id=current_user.id).scalar() or 0.0
            
            # Get badge level
            badge_level = current_user.badge_level or 'Bronze'
            
            return render_template('footprint_dashboard.html',
                weekly_history=weekly_history,
                current_weekly=current_weekly,
                recent_scans=recent_scans,
                total_lifetime=float(total_lifetime),
                badge_level=badge_level
            )
        except Exception as e:
            logging.error(f"Error loading footprint dashboard: {e}")
            flash("Error loading dashboard. Please try again.", "danger")
            return redirect(url_for('index'))
    
    @app.route('/footprint-dashboard/sync', methods=['POST'])
    @login_required
    def sync_footprint_data():
        """Sync all scans to weekly records (for fixing missing data)"""
        try:
            from footprint_updater import sync_all_scans_to_weekly
            count = sync_all_scans_to_weekly()
            flash(f"Synced {count} weekly footprint records. Dashboard should now show your data!", "success")
            return redirect(url_for('footprint_dashboard'))
        except Exception as e:
            logging.error(f"Error syncing footprint data: {e}")
            flash("Error syncing footprint data. Please try again.", "danger")
            return redirect(url_for('footprint_dashboard'))
    
    # ============================================================================
    # INFRASTRUCTURE PROJECTS
    # ============================================================================
    
    @app.route('/projects')
    def projects_list():
        """Display list of infrastructure projects"""
        try:
            status_filter = request.args.get('status', 'all')
            query = InfrastructureProject.query
            
            if status_filter != 'all':
                query = query.filter_by(status=status_filter)
            
            projects = query.order_by(desc(InfrastructureProject.created_at)).limit(20).all()
            
            # Get user contributions if logged in
            user_contributions = {}
            if current_user.is_authenticated:
                for project in projects:
                    contrib = db.session.query(
                        func.sum(ProjectContributor.contribution_weight_grams)
                    ).join(WasteBatch).filter(
                        WasteBatch.linked_project_id == project.id,
                        ProjectContributor.user_id == current_user.id
                    ).scalar() or 0.0
                    
                    is_top = ProjectContributor.query.join(WasteBatch).filter(
                        WasteBatch.linked_project_id == project.id,
                        ProjectContributor.user_id == current_user.id,
                        ProjectContributor.is_top_contributor == True
                    ).first() is not None
                    
                    user_contributions[project.id] = {
                        'weight': float(contrib),
                        'is_top': is_top
                    }
            
            return render_template('projects_list.html',
                projects=projects,
                status_filter=status_filter,
                user_contributions=user_contributions
            )
        except Exception as e:
            logging.error(f"Error loading projects list: {e}")
            flash("Error loading projects. Please try again.", "danger")
            return redirect(url_for('index'))
    
    @app.route('/projects/<project_id>')
    def project_detail(project_id):
        """Display detailed information about a specific project"""
        try:
            project = InfrastructureProject.query.filter_by(project_id=project_id).first_or_404()
            
            # Get contributors
            from models import User
            contributors = db.session.query(
                User.username,
                func.sum(ProjectContributor.contribution_weight_grams).label('total_contribution')
            ).join(ProjectContributor).join(WasteBatch).filter(
                WasteBatch.linked_project_id == project.id
            ).group_by(User.id, User.username).order_by(desc('total_contribution')).limit(10).all()
            
            # Get ledger entries
            ledger_entries = ProjectLedger.query.filter_by(
                project_id=project_id
            ).order_by(ProjectLedger.timestamp).all()
            
            # Calculate progress
            progress = 0.0
            if project.total_plastic_required_grams and project.total_plastic_required_grams > 0:
                progress = (project.total_plastic_allocated_grams / project.total_plastic_required_grams) * 100.0
            
            # Get user contribution if logged in
            user_contribution = None
            is_top_contributor = False
            if current_user.is_authenticated:
                contrib = db.session.query(
                    func.sum(ProjectContributor.contribution_weight_grams)
                ).join(WasteBatch).filter(
                    WasteBatch.linked_project_id == project.id,
                    ProjectContributor.user_id == current_user.id
                ).scalar() or 0.0
                
                user_contribution = float(contrib)
                
                is_top_contributor = ProjectContributor.query.join(WasteBatch).filter(
                    WasteBatch.linked_project_id == project.id,
                    ProjectContributor.user_id == current_user.id,
                    ProjectContributor.is_top_contributor == True
                ).first() is not None
            
            return render_template('project_detail.html',
                project=project,
                contributors=contributors,
                ledger_entries=ledger_entries,
                progress=round(progress, 2),
                user_contribution=user_contribution,
                is_top_contributor=is_top_contributor
            )
        except Exception as e:
            logging.error(f"Error loading project detail: {e}")
            flash("Error loading project details. Please try again.", "danger")
            return redirect(url_for('projects_list'))
    
    # ============================================================================
    # MULTILINGUAL SUPPORT
    # ============================================================================
    
    @app.route('/language/select', methods=['GET', 'POST'])
    @login_required
    def select_language():
        """Language selection screen (first launch or settings)"""
        from localization_manager import get_all_languages
        
        if request.method == 'POST':
            try:
                language = request.form.get('language', 'en')
                
                if language in get_all_languages():
                    current_user.preferred_language = language
                    current_user.onboarding_completed = True  # Mark onboarding as complete
                    db.session.commit()
                    
                    from flask import session
                    session['language'] = language
                    
                    flash("Language selected successfully!", "success")
                    return redirect(url_for('index'))
                else:
                    flash("Invalid language selection", "danger")
            except Exception as e:
                logging.error(f"Error selecting language: {e}")
                db.session.rollback()
                flash("Error selecting language", "danger")
        
        languages = get_all_languages()
        return render_template('language_selection.html', languages=languages)
    
    @app.route('/language/change', methods=['POST'])
    @login_required
    def change_language():
        """Change user's preferred language"""
        try:
            # Get language from form or JSON
            if request.is_json:
                language = request.json.get('language', 'en')
            else:
                language = request.form.get('language', 'en')
            
            if language in ['en', 'hi', 'kn', 'ta', 'mr', 'bn']:
                # Update user preference
                current_user.preferred_language = language
                db.session.commit()
                
                # Store in session for immediate use (MUST be done after commit)
                from flask import session
                session['language'] = language
                session.permanent = True  # Make session persistent
                
                language_names = {
                    'en': 'English',
                    'hi': 'Hindi',
                    'kn': 'Kannada',
                    'ta': 'Tamil',
                    'mr': 'Marathi',
                    'bn': 'Bengali'
                }
                flash(f"Language changed to {language_names.get(language, language)}", "success")
            else:
                flash("Invalid language selection", "danger")
        except Exception as e:
            logging.error(f"Error changing language: {e}")
            db.session.rollback()
            flash("Error changing language", "danger")
        
        # Return JSON for AJAX requests, otherwise redirect
        if request.is_json:
            return jsonify({'success': True, 'language': language, 'message': f'Language changed to {language_names.get(language, language)}'})
        return redirect(request.referrer or url_for('index'))

