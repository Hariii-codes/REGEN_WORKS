"""
Infrastructure Projects Feature - Routes and Logic
Handles infrastructure project dashboard, batch linking, and ledger updates
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import InfrastructureProject, WasteBatch, ProjectContributor, ProjectLedger
from sqlalchemy import func, desc
from blockchain_tracker import get_project_blockchain, get_user_contribution_chain
import uuid
import logging
from datetime import datetime
from firestore_sync import write_ledger_entry

def register_infrastructure_project_routes(app):
    """Register infrastructure project routes"""
    
    @app.route('/infrastructure-projects')
    @login_required
    def infrastructure_projects():
        """
        Infrastructure Projects Dashboard
        Displays all infrastructure projects with user contributions and Google Maps
        """
        try:
            # Auto-seed if no projects exist
            project_count = InfrastructureProject.query.count()
            if project_count == 0:
                from seed_infrastructure_projects import seed_infrastructure_projects
                seed_infrastructure_projects()
            
            # Get all projects
            projects = InfrastructureProject.query.order_by(
                desc(InfrastructureProject.created_at)
            ).all()
            
            # Calculate user contributions for each project
            user_contributions = {}
            top_contributors = {}
            
            for project in projects:
                # Get user's total contribution to this project
                user_contrib = db.session.query(
                    func.sum(ProjectContributor.contribution_weight_grams)
                ).join(WasteBatch).filter(
                    WasteBatch.linked_project_id == project.id,
                    ProjectContributor.user_id == current_user.id
                ).scalar() or 0.0
                
                # Check if user is top contributor
                is_top = ProjectContributor.query.join(WasteBatch).filter(
                    WasteBatch.linked_project_id == project.id,
                    ProjectContributor.user_id == current_user.id,
                    ProjectContributor.is_top_contributor == True
                ).first() is not None
                
                user_contributions[project.id] = {
                    'weight': float(user_contrib),
                    'is_top': is_top
                }
                
                # Get top contributors for this project (top 10%)
                total_contributors = db.session.query(
                    func.count(func.distinct(ProjectContributor.user_id))
                ).join(WasteBatch).filter(
                    WasteBatch.linked_project_id == project.id
                ).scalar() or 0
                
                top_contributors[project.id] = total_contributors > 0 and is_top
            
            return render_template(
                'infrastructure_projects.html',
                projects=projects,
                user_contributions=user_contributions,
                top_contributors=top_contributors
            )
            
        except Exception as e:
            logging.error(f"Error loading infrastructure projects: {e}")
            flash("Error loading projects. Please try again.", "danger")
            return redirect(url_for('index'))
    
    @app.route('/infrastructure-projects/map')
    @login_required
    def infrastructure_projects_map():
        """
        Display a map of all infrastructure projects using OpenLayers (same system as drop points)
        """
        try:
            # Get all projects with locations
            projects = InfrastructureProject.query.filter(
                InfrastructureProject.location_lat.isnot(None),
                InfrastructureProject.location_lng.isnot(None)
            ).all()
            
            # Calculate user contributions for each project
            user_contributions = {}
            for project in projects:
                user_contrib = db.session.query(
                    func.sum(ProjectContributor.contribution_weight_grams)
                ).join(WasteBatch).filter(
                    WasteBatch.linked_project_id == project.id,
                    ProjectContributor.user_id == current_user.id
                ).scalar() or 0.0
                
                user_contributions[project.id] = float(user_contrib)
            
            return render_template(
                'infrastructure_projects_map.html',
                projects=projects,
                user_contributions=user_contributions
            )
        except Exception as e:
            logging.error(f"Error loading infrastructure projects map: {e}")
            flash("Error loading projects map. Please try again.", "danger")
            return redirect(url_for('infrastructure_projects'))
    
    @app.route('/infrastructure-projects/<int:project_id>/blockchain')
    @login_required
    def project_blockchain(project_id):
        """View blockchain for a specific project"""
        try:
            project = InfrastructureProject.query.get_or_404(project_id)
            blockchain = get_project_blockchain(project.project_id)
            
            return render_template(
                'project_blockchain.html',
                project=project,
                blockchain=blockchain
            )
        except Exception as e:
            logging.error(f"Error loading project blockchain: {e}")
            flash("Error loading blockchain. Please try again.", "danger")
            return redirect(url_for('infrastructure_projects'))
    
    @app.route('/my-contributions/blockchain')
    @login_required
    def my_contribution_blockchain():
        """View user's contribution blockchain"""
        try:
            contribution_chains = get_user_contribution_chain(current_user.id)
            
            return render_template(
                'my_contribution_blockchain.html',
                contribution_chains=contribution_chains
            )
        except Exception as e:
            logging.error(f"Error loading contribution blockchain: {e}")
            flash("Error loading contribution blockchain. Please try again.", "danger")
            return redirect(url_for('infrastructure_projects'))
    
    @app.route('/contribute-to-project')
    @app.route('/contribute-to-project/<int:waste_item_id>')
    @login_required
    def contribute_to_project(waste_item_id=0):
        """Page to select and contribute waste item to infrastructure project"""
        try:
            from models import WasteItem
            from datetime import timedelta
            
            # Get project_id from request args
            project_id = request.args.get('project_id', type=int)
            
            waste_item = None
            material_type = 'Various Materials'
            selected_project = None
            
            # Get selected project if provided
            if project_id:
                selected_project = InfrastructureProject.query.get(project_id)
            
            if waste_item_id > 0:
                waste_item = WasteItem.query.get_or_404(waste_item_id)
                
                # Verify ownership
                if waste_item.user_id != current_user.id:
                    flash("You can only contribute your own waste items.", "danger")
                    return redirect(url_for('index'))
                
                material_type = waste_item.material_type or waste_item.material or 'Plastic'
            
            # Get user's recent recyclable waste items (last 30 days, not yet contributed)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_waste_items = WasteItem.query.filter(
                WasteItem.user_id == current_user.id,
                WasteItem.is_recyclable == True,
                WasteItem.created_at >= thirty_days_ago
            ).order_by(WasteItem.created_at.desc()).limit(10).all()
            
            # Get all available projects
            projects = InfrastructureProject.query.filter(
                InfrastructureProject.status.in_(['planned', 'in_progress'])
            ).order_by(InfrastructureProject.created_at.desc()).all()
            
            # Filter projects that need materials
            suitable_projects = []
            
            for project in projects:
                # Check if project still needs materials
                if project.total_plastic_required_grams:
                    allocated = float(project.total_plastic_allocated_grams or 0)
                    required = float(project.total_plastic_required_grams)
                    if allocated < required:
                        suitable_projects.append(project)
                else:
                    suitable_projects.append(project)
            
            return render_template(
                'contribute_to_project.html',
                waste_item=waste_item,
                projects=suitable_projects,
                selected_project=selected_project,
                recent_waste_items=recent_waste_items,
                material_type=material_type
            )
        except Exception as e:
            logging.error(f"Error loading contribute page: {e}")
            flash("Error loading contribution page. Please try again.", "danger")
            return redirect(url_for('index'))
    
    @app.route('/contribute-to-project/<int:waste_item_id>/<int:project_id>', methods=['POST'])
    @app.route('/contribute-to-project/<int:project_id>', defaults={'waste_item_id': 0}, methods=['POST'])
    @login_required
    def submit_contribution(waste_item_id, project_id):
        """Submit contribution of waste item to infrastructure project"""
        try:
            from models import WasteItem
            from auto_batch_creator import link_batch_to_project_auto
            
            project = InfrastructureProject.query.get_or_404(project_id)
            
            if waste_item_id > 0:
                waste_item = WasteItem.query.get_or_404(waste_item_id)
                
                # Verify ownership
                if waste_item.user_id != current_user.id:
                    flash("You can only contribute your own waste items.", "danger")
                    return redirect(url_for('index'))
                
                # Only process recyclable items
                if not waste_item.is_recyclable:
                    flash("Only recyclable items can be contributed to infrastructure projects.", "warning")
                    return redirect(url_for('index'))
                
                # Create or update batch
                from auto_batch_creator import auto_create_batch_from_waste_item
                auto_create_batch_from_waste_item(waste_item.id)
                
                # Find the batch for this waste item
                material_type = waste_item.material_type or waste_item.material or 'Plastic'
                from datetime import timedelta
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                
                batch = WasteBatch.query.filter(
                    WasteBatch.material_type == material_type,
                    WasteBatch.collection_date >= seven_days_ago
                ).order_by(WasteBatch.collection_date.desc()).first()
                
                if batch:
                    # Link batch to selected project
                    if not batch.linked_project_id:
                        link_batch_to_project_auto(batch, project, current_user.id)
                        flash(f"Successfully contributed {waste_item.estimated_weight_grams or 25}g to {project.project_name}!", "success")
                    else:
                        flash(f"This material is already part of a batch linked to another project.", "info")
                else:
                    flash("Batch creation in progress. Your contribution will be linked soon.", "info")
            else:
                # No specific waste item - show message to scan first
                flash("Please scan a recyclable waste item first, then contribute it to this project.", "info")
                return redirect(url_for('index'))
            
            return redirect(url_for('infrastructure_project_detail', project_id=project.id))
            
        except Exception as e:
            logging.error(f"Error submitting contribution: {e}")
            flash("Error submitting contribution. Please try again.", "danger")
            return redirect(url_for('index'))
    
    @app.route('/infrastructure-projects/<int:project_id>')
    @login_required
    def infrastructure_project_detail(project_id):
        """Display detailed information about a specific infrastructure project"""
        project = InfrastructureProject.query.get_or_404(project_id)
        
        # Get batches linked to this project
        batches = WasteBatch.query.filter_by(
            linked_project_id=project.id
        ).order_by(desc(WasteBatch.collection_date)).all()
        
        # Calculate materials needed (aggregate by material type)
        materials_needed = {}
        for batch in batches:
            if batch.material_type:
                if batch.material_type not in materials_needed:
                    materials_needed[batch.material_type] = 0
                materials_needed[batch.material_type] += float(batch.total_weight_grams)
        
        # Get user's contribution
        user_contrib = db.session.query(
            func.sum(ProjectContributor.contribution_weight_grams)
        ).join(WasteBatch).filter(
            WasteBatch.linked_project_id == project.id,
            ProjectContributor.user_id == current_user.id
        ).scalar() or 0.0
        
        # Check if user is top contributor
        is_top = ProjectContributor.query.join(WasteBatch).filter(
            WasteBatch.linked_project_id == project.id,
            ProjectContributor.user_id == current_user.id,
            ProjectContributor.is_top_contributor == True
        ).first() is not None
        
        # Get blockchain for this project
        blockchain = get_project_blockchain(project.project_id)
        
        return render_template(
            'infrastructure_project_detail.html',
            project=project,
            batches=batches,
            materials_needed=materials_needed,
            user_contribution=float(user_contrib),
            is_top_contributor=is_top,
            blockchain=blockchain
        )

def link_batch_to_project(batch_id: str, project_id: str, verified_by: str = None):
    """
    Link a waste batch to an infrastructure project and write to ledger
    
    Args:
        batch_id: Batch UUID/ID
        project_id: Project UUID/ID
        verified_by: User/system that verified the link
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Find batch by batch_id (string UUID)
        batch = WasteBatch.query.filter_by(batch_id=batch_id).first()
        if not batch:
            logging.error(f"Batch not found: {batch_id}")
            return False
        
        # Find project by project_id (string UUID)
        project = InfrastructureProject.query.filter_by(project_id=project_id).first()
        if not project:
            logging.error(f"Project not found: {project_id}")
            return False
        
        # Link batch to project
        batch.linked_project_id = project.id
        batch.status = 'allocated'
        
        # Update project allocated weight
        project.total_plastic_allocated_grams = (
            (project.total_plastic_allocated_grams or 0) + float(batch.total_weight_grams)
        )
        
        db.session.commit()
        
        # Write to Firestore ledger
        if verified_by is None:
            verified_by = f'user_{current_user.id if current_user.is_authenticated else "system"}'
        
        write_ledger_entry(
            project_id=project_id,
            batch_id=batch_id,
            weight=int(batch.total_weight_grams),
            verified_by=verified_by,
            status='allocated'
        )
        
        # Update top contributors
        update_top_contributors(project.id)
        
        logging.info(f"Batch {batch_id} linked to project {project_id}")
        return True
        
    except Exception as e:
        logging.error(f"Error linking batch to project: {e}")
        db.session.rollback()
        return False

def update_top_contributors(project_id: int):
    """
    Update top contributor flags for a project (top 10%)
    
    Args:
        project_id: Project database ID
    """
    try:
        # Get all contributors for this project
        contributors = db.session.query(
            ProjectContributor.user_id,
            func.sum(ProjectContributor.contribution_weight_grams).label('total_contrib')
        ).join(WasteBatch).filter(
            WasteBatch.linked_project_id == project_id
        ).group_by(ProjectContributor.user_id).order_by(
            desc('total_contrib')
        ).all()
        
        if not contributors:
            return
        
        # Calculate top 10% threshold
        total_contributors = len(contributors)
        top_count = max(1, int(total_contributors * 0.1))  # Top 10%, at least 1
        
        # Get top contributors
        top_contributors = contributors[:top_count]
        top_user_ids = [c.user_id for c in top_contributors]
        
        # Update flags
        ProjectContributor.query.join(WasteBatch).filter(
            WasteBatch.linked_project_id == project_id
        ).update({
            ProjectContributor.is_top_contributor: ProjectContributor.user_id.in_(top_user_ids)
        }, synchronize_session=False)
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error updating top contributors: {e}")
        db.session.rollback()

