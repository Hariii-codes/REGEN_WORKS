-- ============================================================================
-- ReGenWorks Database Schema Migrations
-- Features: Plastic Footprint Tracker, Multilingual Support, Infrastructure Projects
-- ============================================================================

-- ============================================================================
-- FEATURE 1: PLASTIC FOOTPRINT TRACKER
-- ============================================================================

-- Add material_type and estimated_weight_grams to waste_item table
ALTER TABLE waste_item 
ADD COLUMN IF NOT EXISTS material_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS estimated_weight_grams DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS ml_confidence_score DECIMAL(5, 2);

-- Create user_plastic_footprint_monthly table
CREATE TABLE IF NOT EXISTS user_plastic_footprint_monthly (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    month DATE NOT NULL, -- First day of the month (YYYY-MM-01)
    total_weight_grams DECIMAL(12, 2) DEFAULT 0,
    comparison_percentage DECIMAL(5, 2) DEFAULT 0, -- % change from previous month
    badge_level VARCHAR(20) DEFAULT 'Bronze', -- Bronze, Silver, Gold, Champion
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, month)
);

CREATE INDEX IF NOT EXISTS idx_footprint_user_month ON user_plastic_footprint_monthly(user_id, month);

-- Create plastic_footprint_scans table for individual scan tracking
CREATE TABLE IF NOT EXISTS plastic_footprint_scans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    waste_item_id INTEGER REFERENCES waste_item(id) ON DELETE SET NULL,
    material_type VARCHAR(50) NOT NULL,
    estimated_weight_grams DECIMAL(10, 2) NOT NULL,
    ml_confidence_score DECIMAL(5, 2),
    manual_override BOOLEAN DEFAULT FALSE, -- True if user manually selected material
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scans_user_timestamp ON plastic_footprint_scans(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_scans_material ON plastic_footprint_scans(material_type);

-- Material weight lookup table (average weights per item type)
CREATE TABLE IF NOT EXISTS material_weight_lookup (
    id SERIAL PRIMARY KEY,
    material_type VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(100), -- e.g., "plastic_bottle", "plastic_bag"
    average_weight_grams DECIMAL(10, 2) NOT NULL,
    min_weight_grams DECIMAL(10, 2),
    max_weight_grams DECIMAL(10, 2),
    confidence_threshold DECIMAL(5, 2) DEFAULT 0.70, -- ML confidence threshold
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default weight lookup values
INSERT INTO material_weight_lookup (material_type, category, average_weight_grams, min_weight_grams, max_weight_grams, confidence_threshold) VALUES
('Plastic', 'plastic_bottle', 25.0, 15.0, 50.0, 0.70),
('Plastic', 'plastic_bag', 5.0, 2.0, 10.0, 0.65),
('Plastic', 'plastic_container', 30.0, 20.0, 100.0, 0.75),
('Paper', 'paper_sheet', 5.0, 2.0, 10.0, 0.70),
('Paper', 'cardboard_box', 200.0, 100.0, 500.0, 0.75),
('Metal', 'aluminum_can', 15.0, 10.0, 25.0, 0.70),
('Metal', 'steel_can', 50.0, 30.0, 100.0, 0.75),
('Glass', 'glass_bottle', 300.0, 200.0, 500.0, 0.75),
('Glass', 'glass_container', 150.0, 100.0, 300.0, 0.70)
ON CONFLICT (material_type) DO NOTHING;

-- ============================================================================
-- FEATURE 2: MULTILINGUAL & LOW-LITERACY SUPPORT
-- ============================================================================

-- Add preferred_language to user table
ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) DEFAULT 'en',
ADD COLUMN IF NOT EXISTS voice_input_enabled BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;

-- Create localization strings table
CREATE TABLE IF NOT EXISTS localization_strings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL,
    language VARCHAR(10) NOT NULL,
    value TEXT NOT NULL,
    context VARCHAR(50), -- 'android', 'web', 'both'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(key, language)
);

CREATE INDEX IF NOT EXISTS idx_localization_key_lang ON localization_strings(key, language);

-- Supported languages: en (English), hi (Hindi), kn (Kannada), ta (Tamil), mr (Marathi)
-- Insert common UI strings (sample - full implementation would have all strings)
INSERT INTO localization_strings (key, language, value, context) VALUES
-- Navigation
('nav.scan', 'en', 'Scan Waste', 'both'),
('nav.scan', 'hi', 'कचरा स्कैन करें', 'both'),
('nav.scan', 'kn', 'ಕಸ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ', 'both'),
('nav.scan', 'ta', 'கழிவு ஸ்கேன் செய்யவும்', 'both'),
('nav.scan', 'mr', 'कचरा स्कॅन करा', 'both'),

('nav.drop_points', 'en', 'Drop Points', 'both'),
('nav.drop_points', 'hi', 'ड्रॉप पॉइंट्स', 'both'),
('nav.drop_points', 'kn', 'ಡ್ರಾಪ್ ಪಾಯಿಂಟ್ಗಳು', 'both'),
('nav.drop_points', 'ta', 'டிராப் புள்ளிகள்', 'both'),
('nav.drop_points', 'mr', 'ड्रॉप पॉइंट्स', 'both'),

('nav.dashboard', 'en', 'Dashboard', 'both'),
('nav.dashboard', 'hi', 'डैशबोर्ड', 'both'),
('nav.dashboard', 'kn', 'ಡ್ಯಾಶ್ಬೋರ್ಡ್', 'both'),
('nav.dashboard', 'ta', 'டாஷ்போர்டு', 'both'),
('nav.dashboard', 'mr', 'डॅशबोर्ड', 'both'),

('nav.rewards', 'en', 'Rewards', 'both'),
('nav.rewards', 'hi', 'इनाम', 'both'),
('nav.rewards', 'kn', 'ಬಹುಮಾನಗಳು', 'both'),
('nav.rewards', 'ta', 'வெகுமதிகள்', 'both'),
('nav.rewards', 'mr', 'बक्षीस', 'both'),

-- Voice commands
('voice.report_waste', 'en', 'Report waste', 'both'),
('voice.report_waste', 'hi', 'कचरा रिपोर्ट करें', 'both'),
('voice.report_waste', 'kn', 'ಕಸ ವರದಿ ಮಾಡಿ', 'both'),
('voice.report_waste', 'ta', 'கழிவு அறிக்கை', 'both'),
('voice.report_waste', 'mr', 'कचरा अहवाल द्या', 'both'),

('voice.search_drop_points', 'en', 'Search drop points', 'both'),
('voice.search_drop_points', 'hi', 'ड्रॉप पॉइंट्स खोजें', 'both'),
('voice.search_drop_points', 'kn', 'ಡ್ರಾಪ್ ಪಾಯಿಂಟ್ಗಳನ್ನು ಹುಡುಕಿ', 'both'),
('voice.search_drop_points', 'ta', 'டிராப் புள்ளிகளைத் தேடுங்கள்', 'both'),
('voice.search_drop_points', 'mr', 'ड्रॉप पॉइंट्स शोधा', 'both'),

-- Common actions
('action.scan', 'en', 'Scan', 'both'),
('action.scan', 'hi', 'स्कैन', 'both'),
('action.scan', 'kn', 'ಸ್ಕ್ಯಾನ್', 'both'),
('action.scan', 'ta', 'ஸ்கேன்', 'both'),
('action.scan', 'mr', 'स्कॅन', 'both'),

('action.submit', 'en', 'Submit', 'both'),
('action.submit', 'hi', 'सबमिट करें', 'both'),
('action.submit', 'kn', 'ಸಲ್ಲಿಸಿ', 'both'),
('action.submit', 'ta', 'சமர்ப்பிக்கவும்', 'both'),
('action.submit', 'mr', 'सबमिट करा', 'both')
ON CONFLICT (key, language) DO NOTHING;

-- ============================================================================
-- FEATURE 3: INFRASTRUCTURE PROJECT FEEDBACK LOOP (Blockchain Transparency)
-- ============================================================================

-- Create waste_batches table
CREATE TABLE IF NOT EXISTS waste_batches (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) UNIQUE NOT NULL, -- Unique batch identifier
    total_weight_grams DECIMAL(12, 2) NOT NULL,
    material_type VARCHAR(50) NOT NULL,
    linked_project_id INTEGER, -- Will reference infrastructure_projects
    collection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'collected', -- collected, processing, allocated, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_batches_project ON waste_batches(linked_project_id);
CREATE INDEX IF NOT EXISTS idx_batches_material ON waste_batches(material_type);
CREATE INDEX IF NOT EXISTS idx_batches_status ON waste_batches(status);

-- Create infrastructure_projects table
CREATE TABLE IF NOT EXISTS infrastructure_projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'planned', -- planned, in_progress, completed, cancelled
    location_lat DECIMAL(10, 8) NOT NULL,
    location_lng DECIMAL(11, 8) NOT NULL,
    description TEXT,
    date_started DATE,
    date_completed DATE,
    total_plastic_required_grams DECIMAL(12, 2),
    total_plastic_allocated_grams DECIMAL(12, 2) DEFAULT 0,
    project_type VARCHAR(50), -- bench, pavement_tile, planter, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON infrastructure_projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_location ON infrastructure_projects(location_lat, location_lng);

-- Create project_contributors table
CREATE TABLE IF NOT EXISTS project_contributors (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    batch_id INTEGER NOT NULL REFERENCES waste_batches(id) ON DELETE CASCADE,
    contribution_weight_grams DECIMAL(10, 2) NOT NULL,
    contribution_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_top_contributor BOOLEAN DEFAULT FALSE, -- Top 10% contributor
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contributors_user ON project_contributors(user_id);
CREATE INDEX IF NOT EXISTS idx_contributors_batch ON project_contributors(batch_id);
CREATE INDEX IF NOT EXISTS idx_contributors_top ON project_contributors(is_top_contributor) WHERE is_top_contributor = TRUE;

-- Create blockchain ledger table (Firestore-like structure for PostgreSQL)
-- This will also be synced to Firebase Firestore for immutable records
CREATE TABLE IF NOT EXISTS project_ledger (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    verified_by VARCHAR(100), -- User ID or system identifier
    batch_reference VARCHAR(50), -- Reference to batch_id
    previous_hash VARCHAR(64), -- Hash of previous ledger entry
    block_hash VARCHAR(64) NOT NULL, -- Hash of this entry
    data JSONB, -- Additional metadata
    firestore_synced BOOLEAN DEFAULT FALSE, -- Track if synced to Firestore
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ledger_project ON project_ledger(project_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_ledger_hash ON project_ledger(block_hash);
CREATE INDEX IF NOT EXISTS idx_ledger_synced ON project_ledger(firestore_synced) WHERE firestore_synced = FALSE;

-- ============================================================================
-- UPDATE USER TABLE FOR BADGE LEVEL
-- ============================================================================

ALTER TABLE "user" 
ADD COLUMN IF NOT EXISTS badge_level VARCHAR(20) DEFAULT 'Bronze';

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Function to update user_plastic_footprint_monthly when a scan is added
CREATE OR REPLACE FUNCTION update_plastic_footprint_monthly()
RETURNS TRIGGER AS $$
DECLARE
    current_month DATE;
    prev_month DATE;
    prev_weight DECIMAL(12, 2);
    comparison_pct DECIMAL(5, 2);
    new_badge VARCHAR(20);
BEGIN
    -- Get current month (first day)
    current_month := DATE_TRUNC('month', NEW.timestamp)::DATE;
    
    -- Insert or update monthly footprint
    INSERT INTO user_plastic_footprint_monthly (user_id, month, total_weight_grams, updated_at)
    VALUES (NEW.user_id, current_month, NEW.estimated_weight_grams, CURRENT_TIMESTAMP)
    ON CONFLICT (user_id, month) 
    DO UPDATE SET 
        total_weight_grams = user_plastic_footprint_monthly.total_weight_grams + NEW.estimated_weight_grams,
        updated_at = CURRENT_TIMESTAMP;
    
    -- Calculate comparison percentage
    prev_month := current_month - INTERVAL '1 month';
    SELECT total_weight_grams INTO prev_weight
    FROM user_plastic_footprint_monthly
    WHERE user_id = NEW.user_id AND month = prev_month;
    
    IF prev_weight IS NULL OR prev_weight = 0 THEN
        comparison_pct := 100.0; -- First month or no previous data
    ELSE
        SELECT total_weight_grams INTO comparison_pct
        FROM user_plastic_footprint_monthly
        WHERE user_id = NEW.user_id AND month = current_month;
        
        comparison_pct := ((comparison_pct - prev_weight) / prev_weight) * 100.0;
    END IF;
    
    -- Update comparison percentage
    UPDATE user_plastic_footprint_monthly
    SET comparison_percentage = comparison_pct
    WHERE user_id = NEW.user_id AND month = current_month;
    
    -- Calculate and update badge level
    SELECT total_weight_grams INTO prev_weight
    FROM user_plastic_footprint_monthly
    WHERE user_id = NEW.user_id AND month = current_month;
    
    -- Badge thresholds (in grams)
    IF prev_weight >= 10000 THEN
        new_badge := 'Champion';
    ELSIF prev_weight >= 5000 THEN
        new_badge := 'Gold';
    ELSIF prev_weight >= 2000 THEN
        new_badge := 'Silver';
    ELSE
        new_badge := 'Bronze';
    END IF;
    
    UPDATE user_plastic_footprint_monthly
    SET badge_level = new_badge
    WHERE user_id = NEW.user_id AND month = current_month;
    
    -- Update user's badge level
    UPDATE "user"
    SET badge_level = new_badge
    WHERE id = NEW.user_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trigger_update_footprint ON plastic_footprint_scans;
CREATE TRIGGER trigger_update_footprint
AFTER INSERT ON plastic_footprint_scans
FOR EACH ROW
EXECUTE FUNCTION update_plastic_footprint_monthly();

-- Function to calculate block hash for ledger entries
CREATE OR REPLACE FUNCTION calculate_ledger_hash(
    p_project_id VARCHAR,
    p_timestamp TIMESTAMP,
    p_status VARCHAR,
    p_verified_by VARCHAR,
    p_batch_reference VARCHAR,
    p_previous_hash VARCHAR,
    p_data JSONB
)
RETURNS VARCHAR AS $$
DECLARE
    hash_input TEXT;
    hash_result VARCHAR(64);
BEGIN
    hash_input := p_project_id || '|' || 
                  p_timestamp::TEXT || '|' || 
                  p_status || '|' || 
                  COALESCE(p_verified_by, '') || '|' || 
                  COALESCE(p_batch_reference, '') || '|' || 
                  COALESCE(p_previous_hash, '') || '|' || 
                  COALESCE(p_data::TEXT, '');
    
    hash_result := ENCODE(DIGEST(hash_input, 'sha256'), 'hex');
    RETURN hash_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS FOR REPORTING
-- ============================================================================

-- View for user footprint dashboard
CREATE OR REPLACE VIEW user_footprint_dashboard AS
SELECT 
    u.id as user_id,
    u.username,
    u.badge_level,
    COALESCE(SUM(pfm.total_weight_grams), 0) as total_lifetime_weight_grams,
    COUNT(DISTINCT pfm.month) as active_months,
    pfm.month as current_month,
    pfm.total_weight_grams as current_month_weight,
    pfm.comparison_percentage,
    pfm.badge_level as monthly_badge
FROM "user" u
LEFT JOIN user_plastic_footprint_monthly pfm ON u.id = pfm.user_id
WHERE pfm.month = DATE_TRUNC('month', CURRENT_DATE)::DATE OR pfm.month IS NULL
GROUP BY u.id, u.username, u.badge_level, pfm.month, pfm.total_weight_grams, pfm.comparison_percentage, pfm.badge_level;

-- View for top contributors per project
CREATE OR REPLACE VIEW project_top_contributors AS
SELECT 
    ip.project_id,
    ip.project_name,
    pc.user_id,
    u.username,
    SUM(pc.contribution_weight_grams) as total_contribution_grams,
    COUNT(pc.id) as contribution_count,
    RANK() OVER (PARTITION BY ip.project_id ORDER BY SUM(pc.contribution_weight_grams) DESC) as contributor_rank
FROM infrastructure_projects ip
JOIN waste_batches wb ON wb.linked_project_id = ip.id
JOIN project_contributors pc ON pc.batch_id = wb.id
JOIN "user" u ON u.id = pc.user_id
WHERE ip.status IN ('in_progress', 'completed')
GROUP BY ip.project_id, ip.project_name, pc.user_id, u.username;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE user_plastic_footprint_monthly IS 'Monthly aggregated plastic footprint data per user';
COMMENT ON TABLE plastic_footprint_scans IS 'Individual waste scan records for footprint tracking';
COMMENT ON TABLE material_weight_lookup IS 'ML model weight estimation lookup table';
COMMENT ON TABLE localization_strings IS 'Multilingual UI strings for Android and Web';
COMMENT ON TABLE waste_batches IS 'Batches of collected waste linked to infrastructure projects';
COMMENT ON TABLE infrastructure_projects IS 'Infrastructure projects built from recycled waste';
COMMENT ON TABLE project_contributors IS 'User contributions to infrastructure projects';
COMMENT ON TABLE project_ledger IS 'Blockchain-like immutable ledger for project updates';

