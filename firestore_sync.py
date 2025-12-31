"""
Firebase Firestore integration for Infrastructure Project Ledger
Provides immutable blockchain-like ledger entries in Firestore
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase Admin SDK not installed. Firestore sync will be disabled.")

# Global Firestore client
_firestore_client = None

def initialize_firestore():
    """Initialize Firebase Admin SDK and Firestore client"""
    global _firestore_client
    
    if not FIREBASE_AVAILABLE:
        logging.warning("Firebase Admin SDK not available. Firestore sync disabled.")
        return False
    
    try:
        # Check if already initialized
        if _firestore_client is not None:
            return True
        
        # Check for JSON environment variable first (for Railway/cloud deployments)
        service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
        
        if service_account_json:
            # Use JSON from environment variable
            import json
            try:
                service_account_dict = json.loads(service_account_json)
                cred = credentials.Certificate(service_account_dict)
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid Firebase service account JSON: {e}")
                return False
        else:
            # Fall back to file path (for local development)
            service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY')
            
            if not service_account_path or not os.path.exists(service_account_path):
                logging.warning("Firebase service account key not found. Firestore sync disabled.")
                return False
            
            # Initialize Firebase Admin
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
        
        # Get Firestore client
        _firestore_client = firestore.client()
        logging.info("Firestore initialized successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error initializing Firestore: {e}")
        return False

def write_ledger_entry(project_id: str, batch_id: str, weight: int, 
                      verified_by: str, status: str, timestamp: Optional[datetime] = None) -> bool:
    """
    Write an immutable ledger entry to Firestore
    
    Args:
        project_id: Project UUID/ID
        batch_id: Batch UUID/ID
        weight: Weight in grams
        verified_by: User/system that verified the entry
        status: Status of the batch/project
        timestamp: Optional timestamp (defaults to now)
        
    Returns:
        True if successful, False otherwise
    """
    if not initialize_firestore():
        return False
    
    if _firestore_client is None:
        return False
    
    try:
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Create ledger entry
        ledger_data = {
            'batch_id': batch_id,
            'weight': weight,
            'verified_by': verified_by,
            'status': status,
            'timestamp': timestamp,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        # Write to Firestore: ledger/<project_id>/<timestamp>
        doc_id = timestamp.strftime('%Y%m%d%H%M%S%f')
        doc_ref = _firestore_client.collection('ledger').document(project_id).collection('entries').document(doc_id)
        doc_ref.set(ledger_data)
        
        logging.info(f"Ledger entry written to Firestore: ledger/{project_id}/{doc_id}")
        return True
        
    except Exception as e:
        logging.error(f"Error writing ledger entry to Firestore: {e}")
        return False

def get_ledger_entries(project_id: str, limit: int = 100) -> list:
    """
    Get ledger entries for a project from Firestore
    
    Args:
        project_id: Project UUID/ID
        limit: Maximum number of entries to retrieve
        
    Returns:
        List of ledger entries
    """
    if not initialize_firestore():
        return []
    
    if _firestore_client is None:
        return []
    
    try:
        entries_ref = _firestore_client.collection('ledger').document(project_id).collection('entries')
        entries = entries_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        result = []
        for entry in entries:
            data = entry.to_dict()
            data['id'] = entry.id
            result.append(data)
        
        return result
        
    except Exception as e:
        logging.error(f"Error reading ledger entries from Firestore: {e}")
        return []

