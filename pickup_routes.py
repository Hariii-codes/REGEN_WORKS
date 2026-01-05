"""
Waste Pickup Service Routes
ISOLATED FEATURE - Does not modify any existing functionality
"""

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import PickupRequest, PickupPartner, PickupTimeSlot, User
from datetime import datetime, date, timedelta
import logging
import uuid
import math

logger = logging.getLogger(__name__)


def register_pickup_routes(app):
    """Register all pickup-related routes (isolated from existing features)"""

    # =========================================================================
    # USER-FACING PICKUP ROUTES
    # =========================================================================

    @app.route('/pickup')
    @login_required
    def pickup_home():
        """Home page for pickup service - shows request form and user's requests"""
        try:
            # Get user's active pickup requests
            active_requests = PickupRequest.query.filter_by(
                user_id=current_user.id
            ).filter(
                PickupRequest.status.in_(['Requested', 'Assigned', 'Scheduled'])
            ).order_by(PickupRequest.created_at.desc()).all()

            # Get user's completed pickup requests
            completed_requests = PickupRequest.query.filter_by(
                user_id=current_user.id
            ).filter(
                PickupRequest.status.in_(['Completed', 'Cancelled'])
            ).order_by(PickupRequest.created_at.desc()).limit(10).all()

            # Get available time slots
            time_slots = PickupTimeSlot.query.filter_by(is_active=True).order_by(
                PickupTimeSlot.display_order
            ).all()

            return render_template('pickup_home.html',
                active_requests=active_requests,
                completed_requests=completed_requests,
                time_slots=time_slots
            )
        except Exception as e:
            logger.error(f"Error loading pickup home: {e}")
            flash("Error loading pickup service. Please try again.", "danger")
            return redirect(url_for('index'))

    @app.route('/pickup/request', methods=['GET', 'POST'])
    @login_required
    def request_pickup():
        """Handle pickup request creation"""
        if request.method == 'POST':
            try:
                # Generate unique request ID
                request_id = f"PU{uuid.uuid4().hex[:12].upper()}"

                # Parse date
                preferred_date = datetime.strptime(
                    request.form.get('preferred_date'),
                    '%Y-%m-%d'
                ).date()

                # Create new pickup request
                pickup = PickupRequest(
                    request_id=request_id,
                    user_id=current_user.id,

                    # Waste details
                    waste_type=request.form.get('waste_type'),
                    estimated_quantity=float(request.form.get('estimated_quantity')),
                    quantity_unit=request.form.get('quantity_unit', 'kg'),
                    item_count=int(request.form.get('item_count')) if request.form.get('item_count') else None,
                    description=request.form.get('description', ''),

                    # Location
                    pickup_address=request.form.get('pickup_address'),
                    pickup_lat=float(request.form.get('pickup_lat')),
                    pickup_lng=float(request.form.get('pickup_lng')),
                    landmark=request.form.get('landmark', ''),
                    area=request.form.get('area', ''),

                    # Time
                    preferred_date=preferred_date,
                    preferred_time_slot=request.form.get('preferred_time_slot'),
                    alternative_time_slot=request.form.get('alternative_time_slot', ''),

                    # Contact
                    contact_name=request.form.get('contact_name'),
                    contact_phone=request.form.get('contact_phone'),

                    status='Requested'
                )

                db.session.add(pickup)
                db.session.commit()

                # Auto-assign to nearest partner (async/simplified)
                assigned_partner = _find_and_assign_nearest_partner(pickup)

                if assigned_partner:
                    flash(f"Pickup request submitted! {assigned_partner.name} will contact you shortly.", "success")
                else:
                    flash("Pickup request submitted! We'll find a partner and contact you soon.", "success")

                return redirect(url_for('pickup_status', request_id=request_id))

            except Exception as e:
                logger.error(f"Error creating pickup request: {e}")
                db.session.rollback()
                flash("Error submitting pickup request. Please try again.", "danger")
                return redirect(url_for('pickup_home'))

        # GET request - show form with pre-filled data if available
        waste_item_id = request.args.get('waste_item_id')
        prefill_data = {}

        if waste_item_id:
            from models import WasteItem
            item = WasteItem.query.get(waste_item_id)
            if item and item.material_type:
                prefill_data['waste_type'] = item.material_type
                if item.estimated_weight_grams:
                    prefill_data['estimated_quantity'] = round(float(item.estimated_weight_grams) / 1000, 2)  # Convert to kg

        time_slots = PickupTimeSlot.query.filter_by(is_active=True).order_by(
            PickupTimeSlot.display_order
        ).all()

        return render_template('pickup_request_form.html',
            time_slots=time_slots,
            prefill_data=prefill_data
        )

    @app.route('/pickup/status/<request_id>')
    @login_required
    def pickup_status(request_id):
        """View status of a specific pickup request"""
        try:
            pickup = PickupRequest.query.filter_by(
                request_id=request_id,
                user_id=current_user.id
            ).first_or_404()

            return render_template('pickup_status.html', pickup=pickup)
        except Exception as e:
            logger.error(f"Error loading pickup status: {e}")
            flash("Error loading pickup status.", "danger")
            return redirect(url_for('pickup_home'))

    @app.route('/pickup/cancel/<request_id>', methods=['POST'])
    @login_required
    def cancel_pickup(request_id):
        """Cancel a pickup request"""
        try:
            pickup = PickupRequest.query.filter_by(
                request_id=request_id,
                user_id=current_user.id
            ).first_or_404()

            # Can only cancel if not already picked up or completed
            if pickup.status in ['Requested', 'Assigned', 'Scheduled']:
                pickup.update_status('Cancelled')
                db.session.commit()
                flash("Pickup request cancelled successfully.", "success")
            else:
                flash("Cannot cancel a pickup that is already in progress or completed.", "warning")

            return redirect(url_for('pickup_home'))
        except Exception as e:
            logger.error(f"Error cancelling pickup: {e}")
            db.session.rollback()
            flash("Error cancelling pickup request.", "danger")
            return redirect(url_for('pickup_home'))

    @app.route('/pickup/rate/<request_id>', methods=['POST'])
    @login_required
    def rate_pickup(request_id):
        """Rate a completed pickup"""
        try:
            pickup = PickupRequest.query.filter_by(
                request_id=request_id,
                user_id=current_user.id,
                status='Completed'
            ).first_or_404()

            rating = int(request.form.get('rating', 5))
            feedback = request.form.get('feedback', '')

            pickup.user_rating = rating
            pickup.user_feedback = feedback
            db.session.commit()

            flash("Thank you for your feedback!", "success")
            return redirect(url_for('pickup_status', request_id=request_id))
        except Exception as e:
            logger.error(f"Error rating pickup: {e}")
            flash("Error submitting rating.", "danger")
            return redirect(url_for('pickup_home'))

    # =========================================================================
    # ADMIN/PARTNER ROUTES
    # =========================================================================

    @app.route('/pickup/admin/partners')
    @login_required
    def pickup_partners_admin():
        """Admin page to manage pickup partners"""
        # TODO: Add admin authentication check
        partners = PickupPartner.query.filter_by(is_active=True).all()
        return render_template('pickup_partners_admin.html', partners=partners)

    @app.route('/pickup/admin/requests')
    @login_required
    def pickup_requests_admin():
        """Admin page to view and manage pickup requests"""
        # TODO: Add admin authentication check
        status_filter = request.args.get('status', 'all')

        query = PickupRequest.query
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)

        requests = query.order_by(PickupRequest.created_at.desc()).limit(50).all()

        return render_template('pickup_requests_admin.html',
            requests=requests,
            status_filter=status_filter
        )

    @app.route('/pickup/admin/assign/<request_id>', methods=['POST'])
    @login_required
    def admin_assign_pickup(request_id):
        """Manually assign a pickup to a partner"""
        # TODO: Add admin authentication check
        try:
            pickup = PickupRequest.query.filter_by(request_id=request_id).first_or_404()

            partner_id = int(request.form.get('partner_id'))
            scheduled_time = request.form.get('scheduled_time')

            pickup.assign_partner(partner_id, scheduled_time)
            db.session.commit()

            flash("Pickup assigned successfully.", "success")
            return redirect(url_for('pickup_requests_admin'))
        except Exception as e:
            logger.error(f"Error assigning pickup: {e}")
            db.session.rollback()
            flash("Error assigning pickup.", "danger")
            return redirect(url_for('pickup_requests_admin'))

    @app.route('/pickup/admin/update-status/<request_id>', methods=['POST'])
    @login_required
    def admin_update_pickup_status(request_id):
        """Update pickup status (for partners/admins)"""
        # TODO: Add admin/partner authentication check
        try:
            pickup = PickupRequest.query.filter_by(request_id=request_id).first_or_404()

            new_status = request.form.get('status')
            notes = request.form.get('notes', '')
            collected_weight = request.form.get('collected_weight')

            pickup.update_status(new_status, notes)

            if collected_weight and new_status == 'Completed':
                pickup.collected_weight_kg = float(collected_weight)

            db.session.commit()
            flash("Pickup status updated.", "success")
            return redirect(url_for('pickup_requests_admin'))
        except Exception as e:
            logger.error(f"Error updating pickup status: {e}")
            db.session.rollback()
            flash("Error updating status.", "danger")
            return redirect(url_for('pickup_requests_admin'))

    # =========================================================================
    # API ENDPOINTS
    # =========================================================================

    @app.route('/api/pickup/available-partners', methods=['GET'])
    @login_required
    def api_available_partners():
        """Get list of active pickup partners (for frontend)"""
        try:
            lat = float(request.args.get('lat'))
            lng = float(request.args.get('lng'))
            waste_type = request.args.get('waste_type', '')

            partners = PickupPartner.query.filter_by(is_active=True).all()

            # Filter by accepted materials
            if waste_type:
                partners = [p for p in partners if waste_type in p.accepted_materials]

            # Calculate distance and filter by service radius
            available_partners = []
            for partner in partners:
                distance = _calculate_distance(lat, lng, partner.base_location_lat, partner.base_location_lng)
                if distance <= partner.service_radius_km:
                    available_partners.append({
                        'id': partner.id,
                        'name': partner.name,
                        'organization_type': partner.organization_type,
                        'distance_km': round(distance, 2),
                        'contact_phone': partner.contact_phone
                    })

            # Sort by distance
            available_partners.sort(key=lambda x: x['distance_km'])

            return jsonify({
                'success': True,
                'partners': available_partners[:5]  # Return top 5 nearest
            })
        except Exception as e:
            logger.error(f"Error getting available partners: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/pickup/create', methods=['POST'])
    @login_required
    def api_create_pickup():
        """API endpoint to create pickup request (AJAX)"""
        try:
            data = request.get_json()

            request_id = f"PU{uuid.uuid4().hex[:12].upper()}"

            pickup = PickupRequest(
                request_id=request_id,
                user_id=current_user.id,
                waste_type=data.get('waste_type'),
                estimated_quantity=float(data.get('estimated_quantity')),
                pickup_address=data.get('pickup_address'),
                pickup_lat=float(data.get('pickup_lat')),
                pickup_lng=float(data.get('pickup_lng')),
                preferred_date=datetime.strptime(data.get('preferred_date'), '%Y-%m-%d').date(),
                preferred_time_slot=data.get('preferred_time_slot'),
                contact_name=data.get('contact_name'),
                contact_phone=data.get('contact_phone'),
                status='Requested'
            )

            db.session.add(pickup)
            db.session.commit()

            # Auto-assign partner
            _find_and_assign_nearest_partner(pickup)

            return jsonify({
                'success': True,
                'request_id': request_id,
                'status': pickup.status,
                'redirect_url': url_for('pickup_status', request_id=request_id)
            })
        except Exception as e:
            logger.error(f"API error creating pickup: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/pickup/status/<request_id>', methods=['GET'])
    @login_required
    def api_pickup_status(request_id):
        """Get pickup status as JSON"""
        try:
            pickup = PickupRequest.query.filter_by(
                request_id=request_id,
                user_id=current_user.id
            ).first_or_404()

            response = {
                'success': True,
                'request_id': pickup.request_id,
                'status': pickup.status,
                'waste_type': pickup.waste_type,
                'preferred_date': pickup.preferred_date.isoformat() if pickup.preferred_date else None,
                'preferred_time_slot': pickup.preferred_time_slot,
                'created_at': pickup.created_at.isoformat(),
                'status_updated_at': pickup.status_updated_at.isoformat()
            }

            if pickup.assigned_partner:
                response['partner'] = {
                    'name': pickup.assigned_partner.name,
                    'contact_phone': pickup.assigned_partner.contact_phone
                }

            return jsonify(response)
        except Exception as e:
            logger.error(f"API error getting pickup status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 404


# =========================================================================
# HELPER FUNCTIONS (Private)
# =========================================================================

def _calculate_distance(lat1, lng1, lat2, lng2):
    """
    Calculate distance between two coordinates using Haversine formula
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lng / 2) ** 2)

    c = 2 * math.asin(math.sqrt(a))
    distance = R * c

    return distance


def _find_and_assign_nearest_partner(pickup):
    """
    Find and assign the nearest available pickup partner
    Simple assignment logic - can be enhanced later
    """
    try:
        # Get all active partners
        partners = PickupPartner.query.filter_by(is_active=True).all()

        # Filter by accepted materials
        matching_partners = [
            p for p in partners
            if pickup.waste_type in p.accepted_materials
        ]

        if not matching_partners:
            return None

        # Find nearest partner
        nearest_partner = None
        min_distance = float('inf')

        for partner in matching_partners:
            distance = _calculate_distance(
                pickup.pickup_lat, pickup.pickup_lng,
                partner.base_location_lat, partner.base_location_lng
            )

            if distance <= partner.service_radius_km and distance < min_distance:
                min_distance = distance
                nearest_partner = partner

        # Assign if found
        if nearest_partner:
            pickup.assign_partner(nearest_partner.id)
            db.session.commit()

        return nearest_partner

    except Exception as e:
        logger.error(f"Error assigning partner: {e}")
        return None
