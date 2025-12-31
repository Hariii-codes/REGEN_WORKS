import os
import uuid
import base64
import re
from io import BytesIO
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from app import db
from models import WasteItem, DropLocation
from gemini_service import analyze_waste
from rewards import award_points_for_drop_off, check_achievements
import logging
from PIL import Image
from datetime import datetime

# Import the route modules for our new features
from tracking import register_tracking_routes
from infrastructure import register_infrastructure_routes

def _get_localized_flash(key, default, category="info"):
    """Helper function to get localized flash message"""
    from localization_helper import get_localized_string, get_current_language
    current_lang = get_current_language()
    message = get_localized_string(key, current_lang, default)
    return message, category

def register_routes(app):
    """Register all application routes"""
    
    @app.route("/", methods=["GET", "POST"])
    def index():
        """Handle home page and waste image uploads from file or webcam"""
        result = None
        image_path = None
        waste_item = None
        
        if request.method == "POST":
            # Check if we have a file upload or webcam image
            file_upload = "file" in request.files and request.files["file"].filename != ""
            webcam_upload = "webcam_image" in request.form and request.form["webcam_image"] and request.form["webcam_image"] != ""
            
            if not file_upload and not webcam_upload:
                from localization_helper import get_localized_string, get_current_language
                current_lang = get_current_language()
                error_msg = get_localized_string('errors.no_image', current_lang, 'No image provided. Please upload an image or use the webcam.')
                flash(error_msg, "danger")
                return redirect(request.url)
            
            try:
                # Generate a unique filename
                filename = f"{uuid.uuid4()}.jpg"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                
                # Process either file upload or webcam image
                if file_upload:
                    # Regular file upload
                    file = request.files["file"]
                    file.save(file_path)
                    
                elif webcam_upload:
                    # Process webcam image (data URL)
                    webcam_data = request.form["webcam_image"]
                    # Extract the base64 data from the data URL
                    # Format typically: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...
                    image_data = re.sub('^data:image/.+;base64,', '', webcam_data)
                    
                    # Decode and save as image file
                    decoded_image = base64.b64decode(image_data)
                    with open(file_path, "wb") as f:
                        f.write(decoded_image)
                    
                    # For some browsers, we might need to rotate the image based on EXIF data
                    try:
                        with Image.open(file_path) as img:
                            img.save(file_path)
                    except Exception as img_e:
                        logging.warning(f"Error processing webcam image: {img_e}")
                
                # Analyze the image using Gemini AI
                analysis_result = analyze_waste(file_path)
                
                if "error" in analysis_result:
                    flash(f"Analysis error: {analysis_result['error']}", "danger")
                    return render_template("index.html")
                
                # Calculate carbon emissions
                from carbon_calculator import calculate_carbon_emissions, get_carbon_summary
                from models import MaterialWeightLookup
                from localization_helper import get_current_language
                
                material_type = analysis_result.get("material", "Plastic")
                current_lang = get_current_language()
                
                # Get weight estimate
                weight_lookup = MaterialWeightLookup.query.filter_by(
                    material_type=material_type
                ).first()
                estimated_weight = 25.0  # Default in grams
                if weight_lookup:
                    estimated_weight = float(weight_lookup.average_weight_grams)
                
                # Determine disposal method based on recyclability
                disposal_method = 'recycling' if analysis_result.get("is_recyclable", False) else 'landfill'
                
                # Calculate carbon emissions
                carbon_data = calculate_carbon_emissions(material_type, estimated_weight, disposal_method)
                carbon_summary = get_carbon_summary(carbon_data, current_lang)
                
                # Add carbon emissions to analysis result
                analysis_result['carbon_emissions'] = carbon_data
                analysis_result['carbon_summary'] = carbon_summary
                
                # Create a new waste item record in the database with additional fields
                waste_item = WasteItem(
                    image_path=file_path.replace("static/", ""),
                    is_recyclable=analysis_result["is_recyclable"],
                    is_ewaste=analysis_result["is_ewaste"],
                    material=analysis_result["material"],
                    summary=analysis_result.get("summary", ""),
                    full_analysis=analysis_result["full_analysis"],
                    recycling_instructions=analysis_result.get("recycling_instructions", ""),
                    environmental_impact=analysis_result.get("environmental_impact", ""),
                    disposal_recommendations=analysis_result.get("disposal_recommendations", "")
                )
                
                # Add material detection results if available
                if "material_detection" in analysis_result:
                    waste_item.material_detection = analysis_result["material_detection"]
                
                # Add material type and weight for tracking
                waste_item.material_type = material_type
                waste_item.estimated_weight_grams = estimated_weight
                
                # Link to user if logged in
                if current_user.is_authenticated:
                    waste_item.user_id = current_user.id
                
                # Save to database
                db.session.add(waste_item)
                db.session.commit()
                
                # Auto-create batch and link to project
                from auto_batch_creator import auto_create_batch_from_waste_item
                auto_create_batch_from_waste_item(waste_item.id)
                
                # Create footprint scan if user is authenticated and material detected
                if current_user.is_authenticated and analysis_result.get("material"):
                    try:
                        from models import PlasticFootprintScan, MaterialWeightLookup
                        from sqlalchemy import func
                        
                        material_type = analysis_result.get("material", "Plastic")
                        
                        # Get weight estimate from lookup table
                        weight_lookup = MaterialWeightLookup.query.filter_by(
                            material_type=material_type
                        ).first()
                        
                        estimated_weight = 25.0  # Default
                        if weight_lookup:
                            estimated_weight = float(weight_lookup.average_weight_grams)
                        
                        # Get ML confidence if available
                        ml_confidence = None
                        if "material_detection" in analysis_result:
                            detection = analysis_result["material_detection"]
                            if isinstance(detection, dict):
                                ml_confidence = detection.get("confidence", 0.0)
                        
                        # Create footprint scan
                        scan = PlasticFootprintScan(
                            user_id=current_user.id,
                            waste_item_id=waste_item.id,
                            material_type=material_type,
                            estimated_weight_grams=estimated_weight,
                            ml_confidence_score=ml_confidence
                        )
                        db.session.add(scan)
                        db.session.commit()
                        
                        # Manually update weekly footprint (in case trigger doesn't exist)
                        try:
                            from footprint_updater import update_weekly_footprint
                            update_weekly_footprint(current_user.id, estimated_weight)
                        except Exception as updater_error:
                            logging.error(f"Error updating weekly footprint: {updater_error}")
                    except Exception as e:
                        logging.error(f"Error creating footprint scan: {e}")
                        # Don't fail the whole request if footprint tracking fails
                
                # Store the waste item ID in session for listing form
                session["last_analyzed_item_id"] = waste_item.id
                
                # Set display paths
                image_path = "/" + file_path
                result = analysis_result
                
            except Exception as e:
                logging.error(f"Error processing image: {e}")
                msg, _ = _get_localized_flash('errors.processing_error', 'Error processing image')
                flash(f"{msg}: {str(e)}", "danger")
        
        return render_template("index.html", result=result, image_path=image_path, waste_item=waste_item)
    
    @app.route("/marketplace")
    def marketplace():
        """Display marketplace listings"""
        items = WasteItem.query.filter_by(is_listed=True).order_by(WasteItem.created_at.desc()).all()
        return render_template("marketplace.html", items=items)
    
    @app.route("/municipality")
    def municipality():
        """Display items routed to municipality"""
        items = WasteItem.query.filter_by(sent_to_municipality=True).order_by(WasteItem.created_at.desc()).all()
        return render_template("municipality.html", items=items)
    
    @app.route("/item/<int:item_id>")
    def item_details(item_id):
        """Display details for a specific item"""
        item = WasteItem.query.get_or_404(item_id)
        return render_template("item_details.html", item=item)
    
    @app.route("/list-item", methods=["GET", "POST"])
    def list_item():
        """Handle marketplace listing form"""
        if "last_analyzed_item_id" not in session:
            msg, _ = _get_localized_flash('errors.no_recent_item', 'No recently analyzed item to list', "warning")
            flash(msg, "warning")
            return redirect(url_for("index"))
        
        item_id = session["last_analyzed_item_id"]
        item = WasteItem.query.get_or_404(item_id)
        
        if request.method == "POST":
            item.title = request.form.get("title")
            item.description = request.form.get("description")
            item.contact_email = request.form.get("contact_email")
            item.contact_phone = request.form.get("contact_phone")
            item.location = request.form.get("location")
            item.is_listed = True
            
            # Note: Items are marked as recyclable if they are recyclable, but
            # sending to municipality is optional and user-initiated, not automatic
            
            db.session.commit()
            msg, _ = _get_localized_flash('messages.item_listed', 'Item listed successfully', "success")
            flash(msg, "success")
            
            # Clear the session variable
            session.pop("last_analyzed_item_id", None)
            
            return redirect(url_for("marketplace"))
        
        return render_template("listing_form.html", item=item)
    
    @app.route("/send-to-municipality/<int:item_id>", methods=["POST"])
    def send_to_municipality(item_id):
        """Route an item to municipality and award rewards for contributing to recycling"""
        item = WasteItem.query.get_or_404(item_id)
        item.sent_to_municipality = True
        item.municipality_status = "Pending"
        db.session.commit()
        
        # Award points to the logged-in user if authenticated
        if current_user.is_authenticated:
            try:
                # Give rewards based on material type
                points = 0
                reward_desc = ""
                
                if item.material.lower() == 'plastic':
                    points = 100
                    reward_desc = "Sending plastic waste for municipal recycling"
                elif item.material.lower() == 'paper':
                    points = 75
                    reward_desc = "Sending paper waste for municipal recycling"
                elif item.material.lower() == 'glass':
                    points = 90
                    reward_desc = "Sending glass waste for municipal recycling"
                elif item.material.lower() == 'metal':
                    points = 120
                    reward_desc = "Sending metal waste for municipal recycling"
                elif item.material.lower() == 'electronic':
                    points = 150
                    reward_desc = "Properly disposing of electronic waste"
                else:
                    points = 50
                    reward_desc = "Sending waste for municipal recycling"
                
                # Create a reward record
                from models import Reward
                reward = Reward(
                    user_id=current_user.id,
                    points=points,
                    description=reward_desc,
                    reward_type="municipality"
                )
                db.session.add(reward)
                
                # Update user's eco points
                current_user.eco_points += points
                db.session.commit()
                
                # Check if the user has earned any achievements
                check_achievements(current_user.id)
                
                msg_template, _ = _get_localized_flash('messages.municipality_success_points', 'Item sent to municipality successfully! You earned {points} eco-points.', "success")
                flash(msg_template.format(points=points), "success")
            except Exception as e:
                logging.error(f"Error awarding points: {e}")
                msg, _ = _get_localized_flash('messages.municipality_success_no_points', 'Item sent to municipality successfully, but there was an error awarding points.', "warning")
                flash(msg, "warning")
        else:
            msg, _ = _get_localized_flash('messages.municipality_success_login', 'Item sent to municipality successfully. Log in to earn eco-points for your contributions!', "info")
            flash(msg, "info")
            
        return redirect(url_for("item_details", item_id=item_id))
    
    @app.route("/update-municipality-status/<int:item_id>", methods=["POST"])
    def update_municipality_status(item_id):
        """Update municipality status (for demo purposes)"""
        item = WasteItem.query.get_or_404(item_id)
        status = request.form.get("status")
        if status in ["Pending", "Accepted", "Rejected"]:
            item.municipality_status = status
            db.session.commit()
            msg_template, _ = _get_localized_flash('messages.status_updated', 'Status updated to {status}', "success")
            flash(msg_template.format(status=status), "success")
        return redirect(url_for("municipality"))
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("error.html", error="Page not found"), 404
    
    @app.route("/drop-points")
    def drop_points():
        """Display map with waste drop points in Bangalore"""
        # Predefined drop points in Bangalore
        drop_points = [
            {
                "name": "Dry Waste Collection Center - Koramangala",
                "lat": 12.9352,
                "lon": 77.6245,
                "address": "Koramangala 3rd Block, Bengaluru",
                "types": ["Plastic", "Paper", "Glass"]
            },
            {
                "name": "E-Waste Collection Center - Indiranagar",
                "lat": 12.9784,
                "lon": 77.6408,
                "address": "100 Feet Road, Indiranagar, Bengaluru",
                "types": ["E-Waste", "Batteries"]
            },
            {
                "name": "Saahas Zero Waste - HSR Layout",
                "lat": 12.9116,
                "lon": 77.6473,
                "address": "HSR Layout, Bengaluru",
                "types": ["Plastic", "Paper", "Organic"]
            },
            {
                "name": "ITC WOW Collection Point - Whitefield",
                "lat": 12.9698,
                "lon": 77.7500,
                "address": "Whitefield, Bengaluru",
                "types": ["Paper", "Cardboard"]
            },
            {
                "name": "BBMP Recycling Center - Jayanagar",
                "lat": 12.9250,
                "lon": 77.5938,
                "address": "Jayanagar 4th Block, Bengaluru",
                "types": ["Plastic", "Metal", "Glass", "Paper"]
            }
        ]
        return render_template("drop_points.html", drop_points=drop_points)

    @app.route("/leaderboards")
    @login_required
    def leaderboards():
        """Display eco-champion leaderboards"""
        from flask_login import current_user

        # Mock leaderboard data (in a real app, this would come from database)
        leaderboard_data = [
            {'username': 'Alex Johnson', 'points': 9875, 'items_recycled': 342, 'badge': 'Champion'},
            {'username': 'Jane Smith', 'points': 8450, 'items_recycled': 298, 'badge': 'Gold'},
            {'username': 'Mike Chen', 'points': 7230, 'items_recycled': 276, 'badge': 'Silver'},
            {'username': 'Sarah Williams', 'points': 6890, 'items_recycled': 255, 'badge': 'Gold'},
            {'username': 'David Martinez', 'points': 5760, 'items_recycled': 223, 'badge': 'Silver'},
        ]

        # Find current user's rank
        user_rank = 24  # Mock rank

        return render_template("leaderboards-eco.html",
                             leaderboard_data=leaderboard_data,
                             current_user=current_user,
                             user_rank=user_rank)

    @app.route("/rewards")
    @login_required
    def rewards():
        """Display rewards store"""
        from flask_login import current_user

        # Mock rewards data (in a real app, this would come from database)
        rewards = [
            {
                'name': 'Amazon Gift Card',
                'points': 2000,
                'category': 'vouchers',
                'description': '$20 gift card for eco-friendly purchases',
                'stock': 15
            },
            {
                'name': 'Tree Sapling Kit',
                'points': 500,
                'category': 'plants',
                'description': 'Grow your own tree with our complete sapling kit',
                'stock': 50
            },
            {
                'name': 'Bamboo Coffee Cup',
                'points': 750,
                'category': 'eco',
                'description': 'Reusable bamboo coffee cup with ReGenWorks logo',
                'stock': 30
            },
        ]

        return render_template("rewards-eco.html",
                             rewards=rewards,
                             current_user=current_user)

    @app.route("/check-in-drop-point", methods=["POST"])
    @login_required
    def check_in_drop_point():
        """Handle user check-ins at drop points"""
        if not current_user.is_authenticated:
            msg, _ = _get_localized_flash('errors.login_required', 'You must be logged in to check in at a drop point', "warning")
            flash(msg, "warning")
            return redirect(url_for("auth.login"))
        
        drop_location_id = request.form.get("drop_location_id")
        waste_type = request.form.get("waste_type")
        notes = request.form.get("notes", "")
        
        if not drop_location_id or not waste_type:
            msg, _ = _get_localized_flash('errors.missing_checkin_info', 'Missing required information for check-in', "danger")
            flash(msg, "danger")
            return redirect(url_for("drop_points"))
        
        try:
            # Create a new waste item for the drop-off
            waste_item = WasteItem(
                user_id=current_user.id,
                material=waste_type,
                is_dropped_off=True,
                drop_location_id=drop_location_id,
                drop_date=datetime.utcnow(),
                description=notes,
                is_recyclable=True  # Assuming items being dropped off are recyclable
            )
            db.session.add(waste_item)
            db.session.commit()
            
            # Award points for the drop-off
            award_points_for_drop_off(current_user.id, waste_item.id, drop_location_id)
            
            # Check if user has earned any achievements
            check_achievements(current_user.id)
            
            msg, _ = _get_localized_flash('messages.checkin_success', "Thank you for your check-in! You've been awarded eco-points for your contribution.", "success")
            flash(msg, "success")
            
        except Exception as e:
            logging.error(f"Error processing check-in: {e}")
            db.session.rollback()
            msg, _ = _get_localized_flash('errors.checkin_error', 'Error processing your check-in. Please try again.', "danger")
            flash(msg, "danger")
            
        return redirect(url_for("drop_points"))
    
    @app.errorhandler(500)
    def server_error(e):
        import traceback
        error_msg = str(e) if e else "Server error"
        logging.error(f"500 Internal Server Error: {error_msg}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return render_template("error.html", error="Server error"), 500
        
    # Register routes for our new features
    register_tracking_routes(app)
    register_infrastructure_routes(app)
    
    # Register new feature web routes
    from new_features_routes import register_new_feature_routes
    register_new_feature_routes(app)