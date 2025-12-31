"""
Automatic Batch Creation and Project Linking
Automatically creates batches from waste items and links them to infrastructure projects
"""

import uuid
import logging
from datetime import datetime
from sqlalchemy import func
from models import db, WasteItem, WasteBatch, InfrastructureProject, ProjectContributor, ProjectLedger
from blockchain_tracker import create_material_journey_block
from firestore_sync import write_ledger_entry

def auto_create_batch_from_waste_item(waste_item_id: int):
    """
    Automatically create a batch from a waste item and link it to a project
    
    Args:
        waste_item_id: ID of the waste item
        
    Returns:
        True if successful, False otherwise
    """
    try:
        waste_item = WasteItem.query.get(waste_item_id)
        if not waste_item:
            logging.error(f"Waste item not found: {waste_item_id}")
            return False
        
        # Only process recyclable items
        if not waste_item.is_recyclable:
            logging.info(f"Waste item {waste_item_id} is not recyclable, skipping batch creation")
            return False
        
        # Get material type
        material_type = waste_item.material_type or waste_item.material or 'Plastic'
        
        # Get weight
        weight = float(waste_item.estimated_weight_grams) if waste_item.estimated_weight_grams else 25.0
        
        # Find or create a batch for this material type (within last 7 days)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Try to find an existing batch with same material type that's not yet allocated
        existing_batch = WasteBatch.query.filter(
            WasteBatch.material_type == material_type,
            WasteBatch.status == 'collected',
            WasteBatch.collection_date >= seven_days_ago
        ).order_by(WasteBatch.collection_date.desc()).first()
        
        if existing_batch:
            # Add to existing batch
            existing_batch.total_weight_grams = float(existing_batch.total_weight_grams) + weight
            batch = existing_batch
            logging.info(f"Added {weight}g to existing batch {batch.batch_id}")
        else:
            # Create new batch
            batch_id = str(uuid.uuid4())
            batch = WasteBatch(
                batch_id=batch_id,
                material_type=material_type,
                total_weight_grams=weight,
                status='collected',
                collection_date=datetime.utcnow()
            )
            db.session.add(batch)
            logging.info(f"Created new batch {batch_id} with {weight}g of {material_type}")
        
        db.session.flush()  # Get batch.id
        
        # Create contributor entry if user is logged in
        if waste_item.user_id:
            # Check if contributor entry already exists
            existing_contrib = ProjectContributor.query.filter_by(
                user_id=waste_item.user_id,
                batch_id=batch.id
            ).first()
            
            if existing_contrib:
                # Update existing contribution
                existing_contrib.contribution_weight_grams = float(existing_contrib.contribution_weight_grams) + weight
            else:
                # Create new contributor entry
                contributor = ProjectContributor(
                    user_id=waste_item.user_id,
                    batch_id=batch.id,
                    contribution_weight_grams=weight,
                    contribution_date=datetime.utcnow()
                )
                db.session.add(contributor)
                logging.info(f"Created contributor entry for user {waste_item.user_id}")
        
        # Auto-link batch to a project if batch reaches threshold (e.g., 1000g or more)
        if float(batch.total_weight_grams) >= 1000.0 and not batch.linked_project_id:
            project = find_suitable_project(material_type)
            if project:
                link_batch_to_project_auto(batch, project, waste_item.user_id)
        
        db.session.commit()
        return True
        
    except Exception as e:
        logging.error(f"Error auto-creating batch from waste item: {e}")
        db.session.rollback()
        return False

def find_suitable_project(material_type: str):
    """
    Find a suitable infrastructure project for a material type
    
    Args:
        material_type: Type of material (Plastic, Paper, Metal, etc.)
        
    Returns:
        InfrastructureProject or None
    """
    try:
        # Find projects that need this material type and are not completed
        projects = InfrastructureProject.query.filter(
            InfrastructureProject.status.in_(['planned', 'in_progress'])
        ).all()
        
        # For now, assign to the first project that needs materials
        # In the future, we could match by material type requirements
        for project in projects:
            # Check if project still needs materials
            if project.total_plastic_required_grams:
                allocated = float(project.total_plastic_allocated_grams or 0)
                required = float(project.total_plastic_required_grams)
                if allocated < required:
                    return project
        
        # If no project found, return the first planned project
        first_project = InfrastructureProject.query.filter_by(
            status='planned'
        ).first()
        
        return first_project
        
    except Exception as e:
        logging.error(f"Error finding suitable project: {e}")
        return None

def link_batch_to_project_auto(batch: WasteBatch, project: InfrastructureProject, user_id: int = None):
    """
    Automatically link a batch to a project and create blockchain entries
    
    Args:
        batch: WasteBatch instance
        project: InfrastructureProject instance
        user_id: Optional user ID for verification
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Link batch to project
        batch.linked_project_id = project.id
        batch.status = 'allocated'
        batch.processing_date = datetime.utcnow()
        
        # Update project allocated weight
        project.total_plastic_allocated_grams = (
            float(project.total_plastic_allocated_grams or 0) + float(batch.total_weight_grams)
        )
        
        # Update project status if needed
        if project.status == 'planned' and project.total_plastic_allocated_grams >= (project.total_plastic_required_grams or 0) * 0.1:
            project.status = 'in_progress'
            if project.date_started is None:
                project.date_started = datetime.utcnow().date()
        
        # Create blockchain entry
        verified_by = f'user_{user_id}' if user_id else 'system'
        
        # Create ledger entry for blockchain
        from blockchain_tracker import calculate_block_hash
        import json as json_lib
        
        # Get previous hash
        previous_entry = ProjectLedger.query.filter_by(
            project_id=project.project_id
        ).order_by(ProjectLedger.timestamp.desc()).first()
        
        previous_hash = previous_entry.block_hash if previous_entry else None
        
        # Create block data
        block_data = {
            'batch_id': batch.batch_id,
            'project_id': project.project_id,
            'action': 'allocated',
            'verified_by': verified_by,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': {
                'weight': float(batch.total_weight_grams),
                'material_type': batch.material_type,
                'auto_linked': True
            }
        }
        
        # Calculate block hash
        block_hash = calculate_block_hash(block_data, previous_hash)
        
        # Create ledger entry
        ledger_entry = ProjectLedger(
            project_id=project.project_id,
            batch_reference=batch.batch_id,
            status='allocated',
            verified_by=verified_by,
            previous_hash=previous_hash,
            block_hash=block_hash,
            data=json_lib.dumps(block_data),
            timestamp=datetime.utcnow()
        )
        
        db.session.add(ledger_entry)
        
        # Write to Firestore ledger
        write_ledger_entry(
            project_id=project.project_id,
            batch_id=batch.batch_id,
            weight=int(batch.total_weight_grams),
            verified_by=verified_by,
            status='allocated'
        )
        
        # Update top contributors
        from infrastructure_projects import update_top_contributors
        update_top_contributors(project.id)
        
        logging.info(f"Auto-linked batch {batch.batch_id} to project {project.project_name}")
        return True
        
    except Exception as e:
        logging.error(f"Error auto-linking batch to project: {e}")
        db.session.rollback()
        return False

def process_pending_batches():
    """
    Process pending batches and link them to projects
    This can be called periodically to auto-link batches
    """
    try:
        # Find batches that are collected but not yet allocated
        pending_batches = WasteBatch.query.filter(
            WasteBatch.status == 'collected',
            WasteBatch.linked_project_id.is_(None)
        ).all()
        
        linked_count = 0
        for batch in pending_batches:
            # Link if batch has enough weight
            if float(batch.total_weight_grams) >= 1000.0:
                project = find_suitable_project(batch.material_type)
                if project:
                    if link_batch_to_project_auto(batch, project):
                        linked_count += 1
        
        if linked_count > 0:
            db.session.commit()
            logging.info(f"Auto-linked {linked_count} batches to projects")
        
        return linked_count
        
    except Exception as e:
        logging.error(f"Error processing pending batches: {e}")
        db.session.rollback()
        return 0

