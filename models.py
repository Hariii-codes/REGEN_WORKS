from datetime import datetime
import hashlib
import json
from app import db, bcrypt
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    full_name = db.Column(db.String(120))
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User status and scores
    is_active = db.Column(db.Boolean, default=True)
    eco_points = db.Column(db.Integer, default=0)
    recycling_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Multilingual & Low-Literacy Support
    preferred_language = db.Column(db.String(10), default='en')
    voice_input_enabled = db.Column(db.Boolean, default=True)
    onboarding_completed = db.Column(db.Boolean, default=False)
    
    # Plastic Footprint Tracker
    badge_level = db.Column(db.String(20), default='Bronze')  # Bronze, Silver, Gold, Champion
    
    # Relationships
    waste_items = db.relationship('WasteItem', backref='user', lazy=True)
    rewards = db.relationship('Reward', backref='user', lazy=True)
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)
    footprint_scans = db.relationship('PlasticFootprintScan', backref='user', lazy=True)
    monthly_footprints = db.relationship('UserPlasticFootprintMonthly', backref='user', lazy=True)
    project_contributions = db.relationship('ProjectContributor', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def award_points(self, points):
        self.eco_points += points
        db.session.commit()
    
    def __repr__(self):
        return f"<User {self.username}>"


class WasteItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(255), nullable=False)
    is_recyclable = db.Column(db.Boolean, default=False)
    is_ewaste = db.Column(db.Boolean, default=False)
    material = db.Column(db.String(100))
    full_analysis = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User relationship
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Additional analysis fields
    summary = db.Column(db.Text)
    recycling_instructions = db.Column(db.Text)
    environmental_impact = db.Column(db.Text)
    disposal_recommendations = db.Column(db.Text)
    
    # Material detection results (stored as JSON string)
    _material_detection = db.Column('material_detection', db.Text, nullable=True)
    
    # Fields for marketplace listings
    is_listed = db.Column(db.Boolean, default=False)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    location = db.Column(db.String(200))
    
    # Municipality routing
    sent_to_municipality = db.Column(db.Boolean, default=False)
    municipality_status = db.Column(db.String(50), default="Not Sent")  # Not Sent, Pending, Accepted, Rejected
    
    # Drop-off tracking
    is_dropped_off = db.Column(db.Boolean, default=False)
    drop_location_id = db.Column(db.Integer, db.ForeignKey('drop_location.id'), nullable=True)
    drop_date = db.Column(db.DateTime, nullable=True)
    
    # Blockchain-like journey tracking
    recycling_completed = db.Column(db.Boolean, default=False)
    recycling_completion_date = db.Column(db.DateTime, nullable=True)
    
    # Plastic Footprint Tracker
    material_type = db.Column(db.String(50), nullable=True)
    estimated_weight_grams = db.Column(db.Numeric(10, 2), nullable=True)
    ml_confidence_score = db.Column(db.Numeric(5, 2), nullable=True)
    
    @property
    def material_detection(self):
        """Getter: Deserialize JSON string to Python dictionary"""
        if self._material_detection:
            return json.loads(self._material_detection)
        return None
    
    @material_detection.setter
    def material_detection(self, value):
        """Setter: Serialize Python dictionary to JSON string"""
        if value is not None:
            self._material_detection = json.dumps(value)
        else:
            self._material_detection = None

    def __repr__(self):
        return f"<WasteItem {self.id}: {'Recyclable' if self.is_recyclable else 'Non-Recyclable'}>"


class DropLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accepted_materials = db.Column(db.String(255))  # Comma-separated list of materials
    
    # Relationships
    waste_items = db.relationship('WasteItem', backref='drop_location', lazy=True)
    
    def __repr__(self):
        return f"<DropLocation {self.name}>"


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    badge_image = db.Column(db.String(255))
    points_awarded = db.Column(db.Integer, default=0)
    
    # Achievement requirements
    required_items = db.Column(db.Integer, default=0)  # Number of items required
    required_material = db.Column(db.String(100))  # Specific material type if applicable
    
    # Relationships
    users = db.relationship('UserAchievement', backref='achievement', lazy=True)
    
    def __repr__(self):
        return f"<Achievement {self.name}>"


class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    earned_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserAchievement user_id={self.user_id} achievement_id={self.achievement_id}>"


class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points = db.Column(db.Integer, default=0)
    description = db.Column(db.String(255), nullable=False)
    reward_type = db.Column(db.String(50), nullable=False)  # 'drop_off', 'listing', 'achievement'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Reward {self.id}: {self.points} points for {self.reward_type}>"


class WasteJourneyBlock(db.Model):
    """
    A block in the blockchain-like waste tracking system.
    Each block represents a stage in the waste item's journey from drop-off to recycling.
    """
    id = db.Column(db.Integer, primary_key=True)
    waste_item_id = db.Column(db.Integer, db.ForeignKey('waste_item.id'), nullable=False)
    
    # Block data
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    stage = db.Column(db.String(50), nullable=False)  # 'drop_off', 'collection', 'sorting', 'processing', 'recycling'
    location = db.Column(db.String(255))
    details = db.Column(db.Text)
    verified_by = db.Column(db.String(100))  # Who verified this stage
    
    # Blockchain properties
    previous_hash = db.Column(db.String(64), nullable=True)  # Hash of the previous block
    block_hash = db.Column(db.String(64), nullable=False)  # Hash of this block
    nonce = db.Column(db.Integer, default=0)  # For proof of work simulation
    
    # Relationships
    waste_item = db.relationship('WasteItem', backref='journey_blocks', lazy=True)
    
    def __init__(self, waste_item_id, stage, location, details, verified_by, previous_hash=None):
        self.waste_item_id = waste_item_id
        self.stage = stage
        self.location = location
        self.details = details
        self.verified_by = verified_by
        self.previous_hash = previous_hash
        self.nonce = 0
        
        # Calculate block hash on creation
        self.block_hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate the hash of this block based on its contents"""
        block_data = {
            'waste_item_id': self.waste_item_id,
            'timestamp': str(self.timestamp),
            'stage': self.stage,
            'location': self.location,
            'details': self.details,
            'verified_by': self.verified_by,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }
        
        # Convert the data to a JSON string and hash it
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty=2):
        """Simulate proof of work by finding a hash with leading zeros"""
        target = '0' * difficulty
        
        while self.block_hash[:difficulty] != target:
            self.nonce += 1
            self.block_hash = self.calculate_hash()
        
        return self.block_hash
    
    def is_valid(self):
        """Verify that the block's hash is valid"""
        return self.block_hash == self.calculate_hash()
    
    def __repr__(self):
        return f"<WasteJourneyBlock {self.id}: {self.stage} for waste_item_id={self.waste_item_id}>"


class InfrastructureReport(db.Model):
    """
    Reports of damaged infrastructure submitted by users through webcam photos.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Report details
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'road', 'street_light', 'water_pipe', 'garbage_bin', etc.
    severity = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    
    # Location details
    location_description = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Image and timestamps
    image_path = db.Column(db.String(255), nullable=False)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # 'pending', 'under_review', 'in_progress', 'resolved', 'rejected'
    status_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    municipality_notes = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('infrastructure_reports', lazy=True))
    
    def __repr__(self):
        return f"<InfrastructureReport {self.id}: {self.title} ({self.status})>"


# ============================================================================
# FEATURE 1: PLASTIC FOOTPRINT TRACKER MODELS
# ============================================================================

class UserPlasticFootprintMonthly(db.Model):
    """Monthly aggregated plastic footprint data per user"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    month = db.Column(db.Date, nullable=False)  # First day of month
    total_weight_grams = db.Column(db.Numeric(12, 2), default=0)
    comparison_percentage = db.Column(db.Numeric(5, 2), default=0)  # % change from previous month
    badge_level = db.Column(db.String(20), default='Bronze')  # Bronze, Silver, Gold, Champion
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'month', name='unique_user_month'),)
    
    def __repr__(self):
        return f"<UserPlasticFootprintMonthly user_id={self.user_id} month={self.month}>"


class PlasticFootprintScan(db.Model):
    """Individual waste scan records for footprint tracking"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    waste_item_id = db.Column(db.Integer, db.ForeignKey('waste_item.id', ondelete='SET NULL'), nullable=True)
    material_type = db.Column(db.String(50), nullable=False)
    estimated_weight_grams = db.Column(db.Numeric(10, 2), nullable=False)
    ml_confidence_score = db.Column(db.Numeric(5, 2), nullable=True)
    manual_override = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PlasticFootprintScan id={self.id} user_id={self.user_id}>"


class MaterialWeightLookup(db.Model):
    """ML model weight estimation lookup table"""
    id = db.Column(db.Integer, primary_key=True)
    material_type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    average_weight_grams = db.Column(db.Numeric(10, 2), nullable=False)
    min_weight_grams = db.Column(db.Numeric(10, 2), nullable=True)
    max_weight_grams = db.Column(db.Numeric(10, 2), nullable=True)
    confidence_threshold = db.Column(db.Numeric(5, 2), default=0.70)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MaterialWeightLookup material_type={self.material_type}>"


# ============================================================================
# FEATURE 2: MULTILINGUAL SUPPORT MODELS
# ============================================================================

class LocalizationString(db.Model):
    """Multilingual UI strings for Android and Web"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False)
    language = db.Column(db.String(10), nullable=False)  # en, hi, kn, ta, mr
    value = db.Column(db.Text, nullable=False)
    context = db.Column(db.String(50), nullable=True)  # 'android', 'web', 'both'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('key', 'language', name='unique_key_language'),)
    
    def __repr__(self):
        return f"<LocalizationString key={self.key} language={self.language}>"


# ============================================================================
# FEATURE 3: INFRASTRUCTURE PROJECT MODELS
# ============================================================================

class InfrastructureProject(db.Model):
    """Infrastructure projects built from recycled waste materials (Plastic, Paper, Metal, Glass, Organic, Textile, Electronic, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), unique=True, nullable=False)
    project_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed, cancelled
    location_lat = db.Column(db.Numeric(10, 8), nullable=False)
    location_lng = db.Column(db.Numeric(11, 8), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_started = db.Column(db.Date, nullable=True)
    date_completed = db.Column(db.Date, nullable=True)
    total_plastic_required_grams = db.Column(db.Numeric(12, 2), nullable=True)  # Total weight required (all material types)
    total_plastic_allocated_grams = db.Column(db.Numeric(12, 2), default=0)  # Total weight allocated (all material types)
    project_type = db.Column(db.String(50), nullable=True)  # bench, pavement_tile, planter, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    batches = db.relationship('WasteBatch', backref='project', lazy=True)
    
    def __repr__(self):
        return f"<InfrastructureProject project_id={self.project_id} status={self.status}>"


class WasteBatch(db.Model):
    """Batches of collected waste linked to infrastructure projects"""
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(50), unique=True, nullable=False)
    total_weight_grams = db.Column(db.Numeric(12, 2), nullable=False)
    material_type = db.Column(db.String(50), nullable=False)
    linked_project_id = db.Column(db.Integer, db.ForeignKey('infrastructure_project.id', ondelete='SET NULL'), nullable=True)
    collection_date = db.Column(db.DateTime, default=datetime.utcnow)
    processing_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='collected')  # collected, processing, allocated, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contributors = db.relationship('ProjectContributor', backref='batch', lazy=True)
    
    def __repr__(self):
        return f"<WasteBatch batch_id={self.batch_id} weight={self.total_weight_grams}>"


class ProjectContributor(db.Model):
    """User contributions to infrastructure projects"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('waste_batch.id', ondelete='CASCADE'), nullable=False)
    contribution_weight_grams = db.Column(db.Numeric(10, 2), nullable=False)
    contribution_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_top_contributor = db.Column(db.Boolean, default=False)  # Top 10% contributor
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ProjectContributor user_id={self.user_id} batch_id={self.batch_id}>"


class ProjectLedger(db.Model):
    """Blockchain-like immutable ledger for project updates"""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False)
    verified_by = db.Column(db.String(100), nullable=True)
    batch_reference = db.Column(db.String(50), nullable=True)
    previous_hash = db.Column(db.String(64), nullable=True)
    block_hash = db.Column(db.String(64), nullable=False)
    data = db.Column(db.JSON, nullable=True)  # Additional metadata as JSON
    firestore_synced = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ProjectLedger project_id={self.project_id} block_hash={self.block_hash[:16]}...>"
