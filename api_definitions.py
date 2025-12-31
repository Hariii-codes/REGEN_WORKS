"""
API Definitions for ReGenWorks New Features
===========================================

This file contains route handlers and API endpoints for:
1. Plastic Footprint Tracker
2. Multilingual & Low-Literacy Support
3. Infrastructure Project Feedback Loop

All endpoints follow RESTful conventions and return JSON responses.
"""

from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from models import User, WasteItem, UserPlasticFootprintMonthly, PlasticFootprintScan
from models import InfrastructureProject, WasteBatch, ProjectContributor, ProjectLedger
from models import LocalizationString
from datetime import datetime, date
from sqlalchemy import func, desc
import hashlib
import json
import logging

# Create blueprints for each feature
footprint_bp = Blueprint('footprint', __name__, url_prefix='/api/footprint')
i18n_bp = Blueprint('i18n', __name__, url_prefix='/api/i18n')
projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

# ============================================================================
# FEATURE 1: PLASTIC FOOTPRINT TRACKER API
# ============================================================================

@footprint_bp.route('/scan/update-footprint', methods=['POST'])
@login_required
def update_footprint():
    """
    POST /api/footprint/scan/update-footprint
    
    Update plastic footprint when a waste item is scanned.
    
    Request Body:
    {
        "waste_item_id": 123,
        "material_type": "Plastic",
        "estimated_weight_grams": 25.5,
        "ml_confidence_score": 0.85,
        "manual_override": false
    }
    
    Response:
    {
        "success": true,
        "scan_id": 456,
        "monthly_total": 1250.5,
        "badge_level": "Silver",
        "comparison_percentage": 15.5
    }
    """
    try:
        data = request.get_json()
        waste_item_id = data.get('waste_item_id')
        material_type = data.get('material_type')
        estimated_weight_grams = data.get('estimated_weight_grams')
        ml_confidence_score = data.get('ml_confidence_score', 0.0)
        manual_override = data.get('manual_override', False)
        
        if not material_type or not estimated_weight_grams:
            return jsonify({
                'success': False,
                'error': 'material_type and estimated_weight_grams are required'
            }), 400
        
        # Create footprint scan record
        scan = PlasticFootprintScan(
            user_id=current_user.id,
            waste_item_id=waste_item_id,
            material_type=material_type,
            estimated_weight_grams=float(estimated_weight_grams),
            ml_confidence_score=float(ml_confidence_score) if ml_confidence_score else None,
            manual_override=manual_override,
            timestamp=datetime.utcnow()
        )
        db.session.add(scan)
        db.session.commit()
        
        # Get updated monthly footprint (trigger will update it)
        current_month = date.today().replace(day=1)
        monthly = UserPlasticFootprintMonthly.query.filter_by(
            user_id=current_user.id,
            month=current_month
        ).first()
        
        if monthly:
            return jsonify({
                'success': True,
                'scan_id': scan.id,
                'monthly_total': float(monthly.total_weight_grams),
                'badge_level': monthly.badge_level,
                'comparison_percentage': float(monthly.comparison_percentage)
            }), 200
        else:
            return jsonify({
                'success': True,
                'scan_id': scan.id,
                'monthly_total': float(estimated_weight_grams),
                'badge_level': 'Bronze',
                'comparison_percentage': 0.0
            }), 200
            
    except Exception as e:
        logging.error(f"Error updating footprint: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@footprint_bp.route('/dashboard', methods=['GET'])
@login_required
def get_footprint_dashboard():
    """
    GET /api/footprint/dashboard
    
    Get user's plastic footprint dashboard data.
    
    Query Parameters:
    - months: Number of months to retrieve (default: 6)
    
    Response:
    {
        "success": true,
        "user_id": 1,
        "badge_level": "Gold",
        "total_lifetime_weight_grams": 8500.5,
        "current_month": {
            "month": "2024-01-01",
            "total_weight_grams": 1250.5,
            "comparison_percentage": 15.5,
            "badge_level": "Silver"
        },
        "monthly_history": [
            {
                "month": "2024-01-01",
                "total_weight_grams": 1250.5,
                "comparison_percentage": 15.5,
                "badge_level": "Silver"
            },
            ...
        ],
        "recent_scans": [
            {
                "id": 456,
                "material_type": "Plastic",
                "estimated_weight_grams": 25.5,
                "timestamp": "2024-01-15T10:30:00Z"
            },
            ...
        ]
    }
    """
    try:
        months = int(request.args.get('months', 6))
        
        # Get user's current badge level
        user = User.query.get(current_user.id)
        
        # Get monthly history
        monthly_history = UserPlasticFootprintMonthly.query.filter_by(
            user_id=current_user.id
        ).order_by(desc(UserPlasticFootprintMonthly.month)).limit(months).all()
        
        # Get current month
        current_month = date.today().replace(day=1)
        current_monthly = UserPlasticFootprintMonthly.query.filter_by(
            user_id=current_user.id,
            month=current_month
        ).first()
        
        # Get recent scans
        recent_scans = PlasticFootprintScan.query.filter_by(
            user_id=current_user.id
        ).order_by(desc(PlasticFootprintScan.timestamp)).limit(10).all()
        
        # Calculate total lifetime weight
        total_lifetime = db.session.query(
            func.sum(UserPlasticFootprintMonthly.total_weight_grams)
        ).filter_by(user_id=current_user.id).scalar() or 0.0
        
        return jsonify({
            'success': True,
            'user_id': current_user.id,
            'badge_level': user.badge_level or 'Bronze',
            'total_lifetime_weight_grams': float(total_lifetime),
            'current_month': {
                'month': current_monthly.month.isoformat() if current_monthly else current_month.isoformat(),
                'total_weight_grams': float(current_monthly.total_weight_grams) if current_monthly else 0.0,
                'comparison_percentage': float(current_monthly.comparison_percentage) if current_monthly else 0.0,
                'badge_level': current_monthly.badge_level if current_monthly else 'Bronze'
            },
            'monthly_history': [
                {
                    'month': m.month.isoformat(),
                    'total_weight_grams': float(m.total_weight_grams),
                    'comparison_percentage': float(m.comparison_percentage),
                    'badge_level': m.badge_level
                }
                for m in monthly_history
            ],
            'recent_scans': [
                {
                    'id': s.id,
                    'material_type': s.material_type,
                    'estimated_weight_grams': float(s.estimated_weight_grams),
                    'timestamp': s.timestamp.isoformat()
                }
                for s in recent_scans
            ]
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting footprint dashboard: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@footprint_bp.route('/weight-lookup', methods=['GET'])
def get_weight_lookup():
    """
    GET /api/footprint/weight-lookup
    
    Get material weight lookup table for ML model.
    
    Query Parameters:
    - material_type: Filter by material type (optional)
    
    Response:
    {
        "success": true,
        "lookup": [
            {
                "material_type": "Plastic",
                "category": "plastic_bottle",
                "average_weight_grams": 25.0,
                "min_weight_grams": 15.0,
                "max_weight_grams": 50.0,
                "confidence_threshold": 0.70
            },
            ...
        ]
    }
    """
    try:
        from models import MaterialWeightLookup
        
        material_type = request.args.get('material_type')
        query = MaterialWeightLookup.query
        
        if material_type:
            query = query.filter_by(material_type=material_type)
        
        lookups = query.all()
        
        return jsonify({
            'success': True,
            'lookup': [
                {
                    'material_type': l.material_type,
                    'category': l.category,
                    'average_weight_grams': float(l.average_weight_grams),
                    'min_weight_grams': float(l.min_weight_grams) if l.min_weight_grams else None,
                    'max_weight_grams': float(l.max_weight_grams) if l.max_weight_grams else None,
                    'confidence_threshold': float(l.confidence_threshold)
                }
                for l in lookups
            ]
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting weight lookup: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# FEATURE 2: MULTILINGUAL & LOW-LITERACY SUPPORT API
# ============================================================================

@i18n_bp.route('/strings', methods=['GET'])
def get_localized_strings():
    """
    GET /api/i18n/strings
    
    Get localized strings for UI.
    
    Query Parameters:
    - language: Language code (en, hi, kn, ta, mr) - default: en
    - context: 'android', 'web', or 'both' - default: 'both'
    - keys: Comma-separated list of keys to retrieve (optional)
    
    Response:
    {
        "success": true,
        "language": "hi",
        "strings": {
            "nav.scan": "कचरा स्कैन करें",
            "nav.drop_points": "ड्रॉप पॉइंट्स",
            ...
        }
    }
    """
    try:
        language = request.args.get('language', 'en')
        context = request.args.get('context', 'both')
        keys_param = request.args.get('keys')
        
        query = LocalizationString.query.filter_by(language=language)
        
        if context != 'both':
            query = query.filter(
                (LocalizationString.context == context) | 
                (LocalizationString.context == 'both')
            )
        
        if keys_param:
            keys_list = [k.strip() for k in keys_param.split(',')]
            query = query.filter(LocalizationString.key.in_(keys_list))
        
        strings = query.all()
        
        result = {s.key: s.value for s in strings}
        
        return jsonify({
            'success': True,
            'language': language,
            'strings': result
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting localized strings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@i18n_bp.route('/user/preferences', methods=['GET', 'POST'])
@login_required
def user_language_preferences():
    """
    GET/POST /api/i18n/user/preferences
    
    Get or update user's language preferences.
    
    GET Response:
    {
        "success": true,
        "preferred_language": "hi",
        "voice_input_enabled": true,
        "onboarding_completed": false
    }
    
    POST Request Body:
    {
        "preferred_language": "hi",
        "voice_input_enabled": true
    }
    """
    try:
        user = User.query.get(current_user.id)
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'preferred_language': user.preferred_language or 'en',
                'voice_input_enabled': getattr(user, 'voice_input_enabled', True),
                'onboarding_completed': getattr(user, 'onboarding_completed', False)
            }), 200
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if 'preferred_language' in data:
                user.preferred_language = data['preferred_language']
            
            if 'voice_input_enabled' in data:
                user.voice_input_enabled = data['voice_input_enabled']
            
            if 'onboarding_completed' in data:
                user.onboarding_completed = data['onboarding_completed']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Preferences updated successfully'
            }), 200
            
    except Exception as e:
        logging.error(f"Error handling language preferences: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@i18n_bp.route('/voice/process', methods=['POST'])
@login_required
def process_voice_command():
    """
    POST /api/i18n/voice/process
    
    Process voice input command.
    
    Request Body:
    {
        "audio_data": "base64_encoded_audio",
        "language": "hi",
        "command_type": "report_waste" | "search_drop_points" | "describe_item"
    }
    
    Response:
    {
        "success": true,
        "transcribed_text": "कचरा रिपोर्ट करें",
        "action": "report_waste",
        "parameters": {}
    }
    """
    try:
        data = request.get_json()
        # Note: Actual voice processing would use SpeechRecognition API
        # This is a placeholder for the structure
        
        transcribed_text = data.get('transcribed_text', '')
        command_type = data.get('command_type')
        
        # Map voice commands to actions
        command_map = {
            'report_waste': 'navigate_to_scan',
            'search_drop_points': 'navigate_to_drop_points',
            'describe_item': 'open_item_description'
        }
        
        action = command_map.get(command_type, 'unknown')
        
        return jsonify({
            'success': True,
            'transcribed_text': transcribed_text,
            'action': action,
            'parameters': {}
        }), 200
        
    except Exception as e:
        logging.error(f"Error processing voice command: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# FEATURE 3: INFRASTRUCTURE PROJECT FEEDBACK LOOP API
# ============================================================================

@projects_bp.route('/list', methods=['GET'])
def list_projects():
    """
    GET /api/projects/list
    
    Get list of infrastructure projects.
    
    Query Parameters:
    - status: Filter by status (planned, in_progress, completed)
    - user_id: Filter projects where user contributed (requires auth)
    - limit: Number of results (default: 20)
    - offset: Pagination offset (default: 0)
    
    Response:
    {
        "success": true,
        "projects": [
            {
                "project_id": "proj_001",
                "project_name": "Recycled Plastic Bench - Central Park",
                "status": "in_progress",
                "location": {
                    "lat": 12.9716,
                    "lng": 77.5946
                },
                "description": "Public bench made from recycled plastic",
                "date_started": "2024-01-15",
                "date_completed": null,
                "total_plastic_required_grams": 50000.0,
                "total_plastic_allocated_grams": 35000.0,
                "project_type": "bench",
                "user_contribution_grams": 1250.5,  // if user_id provided
                "is_top_contributor": false  // if user_id provided
            },
            ...
        ],
        "total": 15,
        "limit": 20,
        "offset": 0
    }
    """
    try:
        status = request.args.get('status')
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        query = InfrastructureProject.query
        
        if status:
            query = query.filter_by(status=status)
        
        total = query.count()
        projects = query.order_by(desc(InfrastructureProject.created_at)).limit(limit).offset(offset).all()
        
        result_projects = []
        for project in projects:
            project_data = {
                'project_id': project.project_id,
                'project_name': project.project_name,
                'status': project.status,
                'location': {
                    'lat': float(project.location_lat),
                    'lng': float(project.location_lng)
                },
                'description': project.description,
                'date_started': project.date_started.isoformat() if project.date_started else None,
                'date_completed': project.date_completed.isoformat() if project.date_completed else None,
                'total_plastic_required_grams': float(project.total_plastic_required_grams) if project.total_plastic_required_grams else None,
                'total_plastic_allocated_grams': float(project.total_plastic_allocated_grams) if project.total_plastic_allocated_grams else 0.0,
                'project_type': project.project_type
            }
            
            # Add user contribution if user_id provided
            if user_id and current_user.is_authenticated and int(user_id) == current_user.id:
                user_contrib = db.session.query(
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
                
                project_data['user_contribution_grams'] = float(user_contrib)
                project_data['is_top_contributor'] = is_top
            
            result_projects.append(project_data)
        
        return jsonify({
            'success': True,
            'projects': result_projects,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logging.error(f"Error listing projects: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@projects_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    GET /api/projects/{project_id}
    
    Get detailed information about a specific project.
    
    Response:
    {
        "success": true,
        "project": {
            "project_id": "proj_001",
            "project_name": "Recycled Plastic Bench - Central Park",
            "status": "in_progress",
            "location": {
                "lat": 12.9716,
                "lng": 77.5946
            },
            "description": "Public bench made from recycled plastic",
            "date_started": "2024-01-15",
            "date_completed": null,
            "total_plastic_required_grams": 50000.0,
            "total_plastic_allocated_grams": 35000.0,
            "project_type": "bench",
            "progress_percentage": 70.0,
            "contributors": [
                {
                    "user_id": 1,
                    "username": "user1",
                    "contribution_grams": 5000.0,
                    "is_top_contributor": true
                },
                ...
            ],
            "ledger_entries": [
                {
                    "timestamp": "2024-01-15T10:30:00Z",
                    "status": "in_progress",
                    "verified_by": "system",
                    "batch_reference": "batch_001",
                    "block_hash": "abc123..."
                },
                ...
            ]
        }
    }
    """
    try:
        project = InfrastructureProject.query.filter_by(project_id=project_id).first_or_404()
        
        # Get contributors
        contributors = db.session.query(
            User.id,
            User.username,
            func.sum(ProjectContributor.contribution_weight_grams).label('total_contribution')
        ).join(ProjectContributor).join(WasteBatch).filter(
            WasteBatch.linked_project_id == project.id
        ).group_by(User.id, User.username).order_by(desc('total_contribution')).all()
        
        # Get top contributor status
        top_contributors = set()
        if contributors:
            total_contrib = sum(c.total_contribution for c in contributors)
            top_10_percent_threshold = total_contrib * 0.1
            cumulative = 0
            for contrib in contributors:
                cumulative += contrib.total_contribution
                if cumulative <= top_10_percent_threshold:
                    top_contributors.add(contrib.id)
        
        # Get ledger entries
        ledger_entries = ProjectLedger.query.filter_by(
            project_id=project_id
        ).order_by(ProjectLedger.timestamp).all()
        
        # Calculate progress
        progress = 0.0
        if project.total_plastic_required_grams and project.total_plastic_required_grams > 0:
            progress = (project.total_plastic_allocated_grams / project.total_plastic_required_grams) * 100.0
        
        return jsonify({
            'success': True,
            'project': {
                'project_id': project.project_id,
                'project_name': project.project_name,
                'status': project.status,
                'location': {
                    'lat': float(project.location_lat),
                    'lng': float(project.location_lng)
                },
                'description': project.description,
                'date_started': project.date_started.isoformat() if project.date_started else None,
                'date_completed': project.date_completed.isoformat() if project.date_completed else None,
                'total_plastic_required_grams': float(project.total_plastic_required_grams) if project.total_plastic_required_grams else None,
                'total_plastic_allocated_grams': float(project.total_plastic_allocated_grams) if project.total_plastic_allocated_grams else 0.0,
                'project_type': project.project_type,
                'progress_percentage': round(progress, 2),
                'contributors': [
                    {
                        'user_id': c.id,
                        'username': c.username,
                        'contribution_grams': float(c.total_contribution),
                        'is_top_contributor': c.id in top_contributors
                    }
                    for c in contributors
                ],
                'ledger_entries': [
                    {
                        'timestamp': le.timestamp.isoformat(),
                        'status': le.status,
                        'verified_by': le.verified_by,
                        'batch_reference': le.batch_reference,
                        'block_hash': le.block_hash
                    }
                    for le in ledger_entries
                ]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@projects_bp.route('/batch/create', methods=['POST'])
@login_required
def create_batch():
    """
    POST /api/projects/batch/create
    
    Create a new waste batch and link to project.
    Admin/municipality endpoint.
    
    Request Body:
    {
        "total_weight_grams": 5000.0,
        "material_type": "Plastic",
        "linked_project_id": 1,
        "waste_item_ids": [123, 124, 125]  // Optional: link to waste items
    }
    
    Response:
    {
        "success": true,
        "batch_id": "batch_001",
        "message": "Batch created successfully"
    }
    """
    try:
        data = request.get_json()
        total_weight_grams = data.get('total_weight_grams')
        material_type = data.get('material_type')
        linked_project_id = data.get('linked_project_id')
        waste_item_ids = data.get('waste_item_ids', [])
        
        if not total_weight_grams or not material_type:
            return jsonify({
                'success': False,
                'error': 'total_weight_grams and material_type are required'
            }), 400
        
        # Generate batch ID
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{current_user.id}"
        
        # Create batch
        batch = WasteBatch(
            batch_id=batch_id,
            total_weight_grams=float(total_weight_grams),
            material_type=material_type,
            linked_project_id=linked_project_id,
            status='collected'
        )
        db.session.add(batch)
        db.session.flush()
        
        # Create contributor records for linked waste items
        if waste_item_ids:
            for item_id in waste_item_ids:
                item = WasteItem.query.get(item_id)
                if item and item.user_id:
                    # Get weight from footprint scan if available
                    scan = PlasticFootprintScan.query.filter_by(
                        waste_item_id=item_id
                    ).first()
                    
                    weight = scan.estimated_weight_grams if scan else (total_weight_grams / len(waste_item_ids))
                    
                    contributor = ProjectContributor(
                        user_id=item.user_id,
                        batch_id=batch.id,
                        contribution_weight_grams=float(weight)
                    )
                    db.session.add(contributor)
        
        # Update project allocated weight
        if linked_project_id:
            project = InfrastructureProject.query.get(linked_project_id)
            if project:
                project.total_plastic_allocated_grams = (
                    (project.total_plastic_allocated_grams or 0) + float(total_weight_grams)
                )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'message': 'Batch created successfully'
        }), 200
        
    except Exception as e:
        logging.error(f"Error creating batch: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@projects_bp.route('/ledger/update', methods=['POST'])
@login_required
def update_ledger():
    """
    POST /api/projects/ledger/update
    
    Add a ledger entry for project update (blockchain-like).
    Also syncs to Firebase Firestore.
    
    Request Body:
    {
        "project_id": "proj_001",
        "status": "in_progress",
        "verified_by": "user_123",
        "batch_reference": "batch_001",
        "data": {
            "notes": "Batch processed and allocated"
        }
    }
    
    Response:
    {
        "success": true,
        "ledger_id": 789,
        "block_hash": "abc123...",
        "firestore_synced": false
    }
    """
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        status = data.get('status')
        verified_by = data.get('verified_by', f'user_{current_user.id}')
        batch_reference = data.get('batch_reference')
        extra_data = data.get('data', {})
        
        if not project_id or not status:
            return jsonify({
                'success': False,
                'error': 'project_id and status are required'
            }), 400
        
        # Get previous hash
        previous_entry = ProjectLedger.query.filter_by(
            project_id=project_id
        ).order_by(desc(ProjectLedger.timestamp)).first()
        
        previous_hash = previous_entry.block_hash if previous_entry else None
        
        # Calculate block hash
        import json as json_lib
        
        block_hash = calculate_ledger_hash(
            project_id,
            datetime.utcnow(),
            status,
            verified_by,
            batch_reference,
            previous_hash,
            json_lib.dumps(extra_data)
        )
        
        # Create ledger entry
        ledger = ProjectLedger(
            project_id=project_id,
            status=status,
            verified_by=verified_by,
            batch_reference=batch_reference,
            previous_hash=previous_hash,
            block_hash=block_hash,
            data=json_lib.dumps(extra_data)
        )
        db.session.add(ledger)
        db.session.commit()
        
        # Sync to Firebase Firestore
        from firestore_sync import write_ledger_entry
        firestore_synced = write_ledger_entry(
            project_id=project_id,
            batch_id=batch_reference or '',
            weight=0,  # Weight will be in extra_data if provided
            verified_by=verified_by,
            status=status
        )
        
        # Update ledger sync status
        if firestore_synced:
            ledger.firestore_synced = True
            db.session.commit()
        
        return jsonify({
            'success': True,
            'ledger_id': ledger.id,
            'block_hash': block_hash,
            'firestore_synced': firestore_synced
        }), 200
        
    except Exception as e:
        logging.error(f"Error updating ledger: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def calculate_ledger_hash(project_id, timestamp, status, verified_by, batch_reference, previous_hash, data):
    """Calculate SHA256 hash for ledger entry"""
    hash_input = f"{project_id}|{timestamp}|{status}|{verified_by}|{batch_reference}|{previous_hash}|{data}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


# ============================================================================
# REGISTER BLUEPRINTS
# ============================================================================

def register_api_routes(app):
    """Register all API blueprints"""
    app.register_blueprint(footprint_bp)
    app.register_blueprint(i18n_bp)
    app.register_blueprint(projects_bp)

