"""
Initialize Pickup Service with Sample Data
Run this script to populate the database with sample pickup partners and time slots
"""

from app import app, db
from models import PickupPartner, PickupTimeSlot
from datetime import datetime

def init_pickup_time_slots():
    """Initialize available time slots for pickup scheduling"""
    time_slots = [
        {
            'slot_label': '9 AM - 12 PM',
            'start_hour': 9,
            'end_hour': 12,
            'display_order': 1
        },
        {
            'slot_label': '12 PM - 3 PM',
            'start_hour': 12,
            'end_hour': 15,
            'display_order': 2
        },
        {
            'slot_label': '3 PM - 6 PM',
            'start_hour': 15,
            'end_hour': 18,
            'display_order': 3
        },
        {
            'slot_label': '6 PM - 8 PM',
            'start_hour': 18,
            'end_hour': 20,
            'display_order': 4
        }
    ]

    for slot_data in time_slots:
        existing = PickupTimeSlot.query.filter_by(slot_label=slot_data['slot_label']).first()
        if not existing:
            slot = PickupTimeSlot(**slot_data)
            db.session.add(slot)
            print(f"✓ Added time slot: {slot_data['slot_label']}")
        else:
            print(f"  Time slot already exists: {slot_data['slot_label']}")

    db.session.commit()
    print("\nTime slots initialized successfully!")


def init_pickup_partners():
    """Initialize sample pickup partners (NGOs, recyclers, collectors)"""

    # Sample partners in Bangalore (adjust locations as needed)
    partners = [
        {
            'partner_id': 'BANG-NGO-001',
            'name': 'Green Earth Foundation',
            'organization_type': 'NGO',
            'contact_person': 'Rajesh Kumar',
            'contact_phone': '+91 98765 43210',
            'contact_email': 'contact@greenearth.org',
            'base_location_lat': 12.9716,
            'base_location_lng': 77.5946,
            'service_radius_km': 15.0,
            'accepted_materials': 'Plastic,Paper,Metal,Glass,Electronic',
            'operating_hours': '9 AM - 6 PM'
        },
        {
            'partner_id': 'BANG-REC-002',
            'name': 'EcoRecycle Solutions',
            'organization_type': 'Recycler',
            'contact_person': 'Priya Sharma',
            'contact_phone': '+91 98765 43211',
            'contact_email': 'info@ecorecycle.in',
            'base_location_lat': 12.9352,
            'base_location_lng': 77.6245,
            'service_radius_km': 20.0,
            'accepted_materials': 'Plastic,Paper,Metal,Glass,Textile,Organic,Mixed',
            'operating_hours': '8 AM - 8 PM'
        },
        {
            'partner_id': 'BANG-MUN-003',
            'name': 'BBMP Ward 45 Collection',
            'organization_type': 'Municipality',
            'contact_person': 'Municipal Office',
            'contact_phone': '+91 98765 43212',
            'contact_email': 'ward45@bbmp.gov.in',
            'base_location_lat': 12.9141,
            'base_location_lng': 77.6101,
            'service_radius_km': 10.0,
            'accepted_materials': 'Plastic,Paper,Glass,Organic,Mixed',
            'operating_hours': '6 AM - 2 PM'
        },
        {
            'partner_id': 'BANG-PVT-004',
            'name': 'Wise Waste Collectors',
            'organization_type': 'Private',
            'contact_person': 'Anand Reddy',
            'contact_phone': '+91 98765 43213',
            'contact_email': 'wise@wastecollectors.com',
            'base_location_lat': 12.9784,
            'base_location_lng': 77.6408,
            'service_radius_km': 12.0,
            'accepted_materials': 'Electronic,Metal,Plastic,Paper',
            'operating_hours': '10 AM - 7 PM'
        },
        {
            'partner_id': 'BANG-NGO-005',
            'name': 'Saahas Zero Waste',
            'organization_type': 'NGO',
            'contact_person': 'Archana Sharma',
            'contact_phone': '+91 98765 43214',
            'contact_email': 'contact@saahas.org',
            'base_location_lat': 12.9081,
            'base_location_lng': 77.5976,
            'service_radius_km': 18.0,
            'accepted_materials': 'Plastic,Paper,Glass,Metal,Textile,Organic',
            'operating_hours': '9 AM - 5 PM'
        }
    ]

    for partner_data in partners:
        existing = PickupPartner.query.filter_by(partner_id=partner_data['partner_id']).first()
        if not existing:
            partner = PickupPartner(**partner_data)
            db.session.add(partner)
            print(f"✓ Added partner: {partner_data['name']} ({partner_data['organization_type']})")
        else:
            print(f"  Partner already exists: {partner_data['name']}")

    db.session.commit()
    print("\nPickup partners initialized successfully!")


def main():
    """Main initialization function"""
    print("=" * 60)
    print("ReGenWorks Pickup Service - Data Initialization")
    print("=" * 60)
    print()

    with app.app_context():
        print("1. Initializing pickup time slots...")
        print("-" * 60)
        init_pickup_time_slots()
        print()

        print("2. Initializing pickup partners...")
        print("-" * 60)
        init_pickup_partners()
        print()

        print("=" * 60)
        print("✓ Pickup service data initialization complete!")
        print("=" * 60)
        print()
        print("The pickup service is now ready with:")
        print(f"  • {PickupTimeSlot.query.count()} time slots")
        print(f"  • {PickupPartner.query.count()} pickup partners")
        print()
        print("You can now use the pickup service at /pickup")
        print()


if __name__ == '__main__':
    main()
