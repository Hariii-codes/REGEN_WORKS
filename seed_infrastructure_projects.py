"""
Seed script to create sample infrastructure projects
Run this to populate the database with example projects
"""

from app import app, db
from models import InfrastructureProject
from datetime import datetime, date
import uuid

def seed_infrastructure_projects():
    """Create sample infrastructure projects"""
    with app.app_context():
        # Check if projects already exist
        existing = InfrastructureProject.query.count()
        if existing > 0:
            print(f"Found {existing} existing projects. Skipping seed.")
            return
        
        # Sample projects
        projects = [
            {
                'project_id': str(uuid.uuid4()),
                'project_name': 'Community Park Bench',
                'description': 'A beautiful park bench made from recycled materials (plastic, metal, and wood), providing seating for the community park.',
                'status': 'in_progress',
                'location_lat': 12.9716,  # Bangalore coordinates
                'location_lng': 77.5946,
                'date_started': date(2024, 1, 15),
                'total_plastic_required_grams': 50000,  # Total weight required (all materials)
                'total_plastic_allocated_grams': 25000,  # Total weight allocated (all materials)
                'project_type': 'bench'
            },
            {
                'project_id': str(uuid.uuid4()),
                'project_name': 'Recycled Pavement Tiles',
                'description': 'Durable pavement tiles made from recycled materials (plastic, glass, and rubber), installed in the main market area.',
                'status': 'planned',
                'location_lat': 12.9352,
                'location_lng': 77.6245,
                'date_started': None,
                'total_plastic_required_grams': 100000,  # Total weight required (all materials)
                'total_plastic_allocated_grams': 15000,  # Total weight allocated (all materials)
                'project_type': 'pavement_tile'
            },
            {
                'project_id': str(uuid.uuid4()),
                'project_name': 'Garden Planters',
                'description': 'Decorative planters for the community garden, made from recycled materials (plastic, ceramic, and metal).',
                'status': 'completed',
                'location_lat': 12.9141,
                'location_lng': 77.6411,
                'date_started': date(2023, 11, 1),
                'date_completed': date(2023, 12, 20),
                'total_plastic_required_grams': 30000,  # Total weight required (all materials)
                'total_plastic_allocated_grams': 30000,  # Total weight allocated (all materials)
                'project_type': 'planter'
            },
            {
                'project_id': str(uuid.uuid4()),
                'project_name': 'School Playground Equipment',
                'description': 'Safe playground equipment for local school, constructed from recycled materials (plastic, metal, and rubber).',
                'status': 'in_progress',
                'location_lat': 12.8994,
                'location_lng': 77.5974,
                'date_started': date(2024, 2, 1),
                'total_plastic_required_grams': 75000,  # Total weight required (all materials)
                'total_plastic_allocated_grams': 40000,  # Total weight allocated (all materials)
                'project_type': 'playground'
            },
            {
                'project_id': str(uuid.uuid4()),
                'project_name': 'Bus Stop Shelter',
                'description': 'Weather-resistant bus stop shelter made from recycled materials (plastic, metal, and glass), providing protection for commuters.',
                'status': 'planned',
                'location_lat': 12.9538,
                'location_lng': 77.5806,
                'date_started': None,
                'total_plastic_required_grams': 80000,  # Total weight required (all materials)
                'total_plastic_allocated_grams': 5000,  # Total weight allocated (all materials)
                'project_type': 'shelter'
            }
        ]
        
        for project_data in projects:
            project = InfrastructureProject(**project_data)
            db.session.add(project)
        
        db.session.commit()
        print(f"✓ Created {len(projects)} infrastructure projects")
        print("\nProjects created:")
        for p in projects:
            print(f"  - {p['project_name']} ({p['status']})")

if __name__ == "__main__":
    seed_infrastructure_projects()

