"""
Blockchain-like Material Tracking System
Tracks the complete journey of materials from waste items to infrastructure projects
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import func
from models import (
    db, WasteItem, WasteBatch, InfrastructureProject, 
    ProjectContributor, ProjectLedger, User
)

def calculate_block_hash(data: Dict[str, Any], previous_hash: Optional[str] = None) -> str:
    """
    Calculate SHA-256 hash for a blockchain block
    
    Args:
        data: Block data dictionary
        previous_hash: Hash of previous block (for chain linking)
        
    Returns:
        SHA-256 hash string
    """
    # Create a deterministic string representation
    block_string = json.dumps(data, sort_keys=True, default=str)
    if previous_hash:
        block_string = f"{previous_hash}{block_string}"
    
    return hashlib.sha256(block_string.encode()).hexdigest()

def create_material_journey_block(
    waste_item_id: int,
    batch_id: str,
    project_id: str,
    action: str,
    verified_by: str,
    metadata: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Create a blockchain block for material journey tracking
    
    Args:
        waste_item_id: ID of the waste item
        batch_id: Batch ID
        project_id: Project ID
        action: Action type (scanned, batched, allocated, completed)
        verified_by: User/system that verified the action
        metadata: Additional metadata
        
    Returns:
        Block dictionary with hash
    """
    try:
        # Get previous block hash for this material journey
        previous_block = ProjectLedger.query.filter_by(
            project_id=project_id
        ).order_by(ProjectLedger.timestamp.desc()).first()
        
        previous_hash = previous_block.block_hash if previous_block else None
        
        # Create block data
        block_data = {
            'waste_item_id': waste_item_id,
            'batch_id': batch_id,
            'project_id': project_id,
            'action': action,
            'verified_by': verified_by,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        # Calculate block hash
        block_hash = calculate_block_hash(block_data, previous_hash)
        
        # Create ledger entry
        ledger_entry = ProjectLedger(
            project_id=project_id,
            batch_reference=batch_id,
            status=action,
            verified_by=verified_by,
            previous_hash=previous_hash,
            block_hash=block_hash,
            data=json.dumps(block_data),
            timestamp=datetime.utcnow()
        )
        
        db.session.add(ledger_entry)
        db.session.commit()
        
        # Sync to Firestore
        from firestore_sync import write_ledger_entry
        write_ledger_entry(
            project_id=project_id,
            batch_id=batch_id,
            weight=0,  # Will be updated from batch
            verified_by=verified_by,
            status=action
        )
        
        return {
            'block_hash': block_hash,
            'previous_hash': previous_hash,
            'data': block_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error creating material journey block: {e}")
        db.session.rollback()
        return None

def get_material_journey(waste_item_id: int) -> List[Dict]:
    """
    Get the complete blockchain-like journey of a material from waste item to infrastructure
    
    Args:
        waste_item_id: ID of the waste item
        
    Returns:
        List of journey steps (blocks)
    """
    try:
        waste_item = WasteItem.query.get(waste_item_id)
        if not waste_item:
            return []
        
        journey = []
        
        # Step 1: Waste Item Scanned
        journey.append({
            'step': 1,
            'action': 'scanned',
            'description': f'Waste item scanned and analyzed',
            'material': waste_item.material or 'Unknown',
            'weight': float(waste_item.estimated_weight_grams) if waste_item.estimated_weight_grams else 0,
            'timestamp': waste_item.created_at.isoformat() if waste_item.created_at else None,
            'verified_by': f'user_{waste_item.user_id}' if waste_item.user_id else 'system',
            'status': 'completed',
            'block_type': 'waste_item'
        })
        
        # Step 2: Find if item is in a batch
        # This requires a link table - for now, we'll check via material type and date
        batches = WasteBatch.query.filter_by(
            material_type=waste_item.material or 'Plastic'
        ).filter(
            WasteBatch.collection_date >= waste_item.created_at
        ).all()
        
        for batch in batches:
            # Step 2: Batched
            journey.append({
                'step': len(journey) + 1,
                'action': 'batched',
                'description': f'Material added to batch {batch.batch_id}',
                'batch_id': batch.batch_id,
                'material': batch.material_type,
                'weight': float(batch.total_weight_grams),
                'timestamp': batch.collection_date.isoformat() if batch.collection_date else None,
                'verified_by': 'system',
                'status': batch.status,
                'block_type': 'batch'
            })
            
            # Step 3: Check if batch is linked to project
            if batch.linked_project_id:
                project = InfrastructureProject.query.get(batch.linked_project_id)
                if project:
                    # Get ledger entries for this project
                    ledger_entries = ProjectLedger.query.filter_by(
                        project_id=project.project_id,
                        batch_reference=batch.batch_id
                    ).order_by(ProjectLedger.timestamp).all()
                    
                    for entry in ledger_entries:
                        journey.append({
                            'step': len(journey) + 1,
                            'action': entry.status,
                            'description': f'Material allocated to project: {project.project_name}',
                            'project_id': project.project_id,
                            'project_name': project.project_name,
                            'batch_id': batch.batch_id,
                            'timestamp': entry.timestamp.isoformat() if entry.timestamp else None,
                            'verified_by': entry.verified_by,
                            'status': entry.status,
                            'block_hash': entry.block_hash,
                            'previous_hash': entry.previous_hash,
                            'block_type': 'ledger'
                        })
        
        return journey
        
    except Exception as e:
        logging.error(f"Error getting material journey: {e}")
        return []

def get_project_blockchain(project_id: str) -> List[Dict]:
    """
    Get the complete blockchain for an infrastructure project
    
    Args:
        project_id: Project UUID/ID
        
    Returns:
        List of blockchain blocks
    """
    try:
        project = InfrastructureProject.query.filter_by(project_id=project_id).first()
        if not project:
            return []
        
        # Get all ledger entries for this project
        ledger_entries = ProjectLedger.query.filter_by(
            project_id=project_id
        ).order_by(ProjectLedger.timestamp).all()
        
        blockchain = []
        for i, entry in enumerate(ledger_entries):
            block_data = json.loads(entry.data) if entry.data else {}
            
            blockchain.append({
                'block_number': i + 1,
                'block_hash': entry.block_hash,
                'previous_hash': entry.previous_hash,
                'timestamp': entry.timestamp.isoformat() if entry.timestamp else None,
                'action': entry.status,
                'verified_by': entry.verified_by,
                'batch_id': entry.batch_reference,
                'data': block_data,
                'is_valid': _validate_block(entry, ledger_entries[i-1] if i > 0 else None)
            })
        
        return blockchain
        
    except Exception as e:
        logging.error(f"Error getting project blockchain: {e}")
        return []

def _validate_block(block: ProjectLedger, previous_block: Optional[ProjectLedger]) -> bool:
    """
    Validate a blockchain block by checking hash integrity
    
    Args:
        block: Current block
        previous_block: Previous block in chain
        
    Returns:
        True if block is valid, False otherwise
    """
    try:
        if previous_block and block.previous_hash != previous_block.block_hash:
            return False
        
        # Recalculate hash to verify
        block_data = json.loads(block.data) if block.data else {}
        calculated_hash = calculate_block_hash(block_data, block.previous_hash)
        
        return calculated_hash == block.block_hash
        
    except Exception as e:
        logging.error(f"Error validating block: {e}")
        return False

def get_user_contribution_chain(user_id: int) -> List[Dict]:
    """
    Get the complete contribution chain for a user showing their materials' journey
    
    Args:
        user_id: User ID
        
    Returns:
        List of contribution chains
    """
    try:
        chains = []
        
        # Get contributions from ProjectContributor
        contributions = ProjectContributor.query.filter_by(
            user_id=user_id
        ).all()
        
        for contrib in contributions:
            batch = WasteBatch.query.get(contrib.batch_id)
            if not batch:
                continue
            
            chain = {
                'contribution_id': contrib.id,
                'weight': float(contrib.contribution_weight_grams),
                'date': contrib.contribution_date.isoformat() if contrib.contribution_date else None,
                'batch': {
                    'batch_id': batch.batch_id,
                    'material': batch.material_type,
                    'total_weight': float(batch.total_weight_grams),
                    'status': batch.status
                }
            }
            
            if batch.linked_project_id:
                project = InfrastructureProject.query.get(batch.linked_project_id)
                if project:
                    chain['project'] = {
                        'project_id': project.project_id,
                        'project_name': project.project_name,
                        'status': project.status
                    }
                    
                    # Get blockchain for this project
                    chain['blockchain'] = get_project_blockchain(project.project_id)
            
            chains.append(chain)
        
        # Also get waste items that haven't been batched yet
        from models import WasteItem
        waste_items = WasteItem.query.filter_by(
            user_id=user_id,
            is_recyclable=True
        ).order_by(WasteItem.created_at.desc()).limit(20).all()
        
        for item in waste_items:
            # Check if this item is already in a batch
            already_in_chain = False
            for chain in chains:
                if chain.get('waste_item_id') == item.id:
                    already_in_chain = True
                    break
            
            if not already_in_chain:
                # Create a chain entry for unbatched items
                chain = {
                    'waste_item_id': item.id,
                    'weight': float(item.estimated_weight_grams) if item.estimated_weight_grams else 0,
                    'date': item.created_at.isoformat() if item.created_at else None,
                    'material': item.material_type or item.material or 'Unknown',
                    'status': 'collected',
                    'batch': None,
                    'project': None
                }
                chains.append(chain)
        
        # Sort by date (newest first)
        chains.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return chains
        
    except Exception as e:
        logging.error(f"Error getting user contribution chain: {e}")
        return []

