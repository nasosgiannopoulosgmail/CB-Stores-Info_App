-- Coffee-Berry Stores Management System Database Schema
-- PostgreSQL 15+ with PostGIS 3.3+

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Stores Table
-- ============================================
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    
    -- External system keys
    entersoft_key VARCHAR(100) UNIQUE,
    inorder_key VARCHAR(100) UNIQUE,
    future_proof_key VARCHAR(100) UNIQUE,
    
    -- Current franchisee
    current_franchisee_id INTEGER REFERENCES franchisees(id) ON DELETE SET NULL,
    
    -- Contact information
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    
    -- Status
    active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index on store location
CREATE INDEX idx_stores_location ON stores USING GIST (
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
);

-- Indexes on external keys
CREATE INDEX idx_stores_entersoft ON stores(entersoft_key) WHERE entersoft_key IS NOT NULL;
CREATE INDEX idx_stores_inorder ON stores(inorder_key) WHERE inorder_key IS NOT NULL;
CREATE INDEX idx_stores_future_proof ON stores(future_proof_key) WHERE future_proof_key IS NOT NULL;
CREATE INDEX idx_stores_active ON stores(active) WHERE active = true;
CREATE INDEX idx_stores_franchisee ON stores(current_franchisee_id) WHERE current_franchisee_id IS NOT NULL;

-- ============================================
-- Franchisees Table
-- ============================================
CREATE TABLE franchisees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    
    -- External system keys
    entersoft_key VARCHAR(100) UNIQUE,
    inorder_key VARCHAR(100) UNIQUE,
    future_proof_key VARCHAR(100) UNIQUE,
    
    -- Contact information
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    
    -- Status
    active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_franchisees_active ON franchisees(active) WHERE active = true;

-- ============================================
-- Polygon Versions Table (with versioning)
-- ============================================
CREATE TABLE polygon_versions (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    polygon_type VARCHAR(20) NOT NULL CHECK (polygon_type IN ('dedicated', 'delivery')),
    
    -- PostGIS geometry (POLYGON in WGS84/EPSG:4326)
    geometry GEOMETRY(POLYGON, 4326) NOT NULL,
    
    -- Versioning fields
    version_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER, -- user_id if user management is added
    inactive BOOLEAN DEFAULT false,
    is_current BOOLEAN DEFAULT false,
    
    -- Metadata
    notes TEXT,
    
    -- Ensure unique version numbers per store+type
    UNIQUE(store_id, polygon_type, version_number)
);

-- Spatial index for geometry queries (critical for performance)
CREATE INDEX idx_polygon_geometry ON polygon_versions USING GIST(geometry);

-- Indexes for common queries
CREATE INDEX idx_polygon_store_type ON polygon_versions(store_id, polygon_type);
CREATE INDEX idx_polygon_current ON polygon_versions(store_id, polygon_type, is_current) 
    WHERE is_current = true AND inactive = false;

-- Unique constraint: only one current version per store+type
CREATE UNIQUE INDEX idx_polygon_current_unique 
    ON polygon_versions(store_id, polygon_type) 
    WHERE is_current = true AND inactive = false;

-- Index for version history queries
CREATE INDEX idx_polygon_created_at ON polygon_versions(created_at DESC);

-- ============================================
-- Store Schedules Table
-- ============================================
CREATE TABLE store_schedules (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Day of week: 0=Monday, 1=Tuesday, ..., 6=Sunday
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    
    -- Multiple time ranges per day stored as JSONB
    -- Format: [{"start": "08:00", "end": "14:00"}, {"start": "17:00", "end": "20:00"}]
    time_ranges JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- Special dates (holidays, closures)
    is_holiday BOOLEAN DEFAULT false,
    date_override DATE, -- For specific date overrides
    
    -- Status
    active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- One schedule per store per day (unless date_override is used)
    UNIQUE(store_id, day_of_week, date_override) NULLS NOT DISTINCT
);

CREATE INDEX idx_schedules_store_day ON store_schedules(store_id, day_of_week) WHERE active = true;
CREATE INDEX idx_schedules_date_override ON store_schedules(store_id, date_override) WHERE date_override IS NOT NULL;

-- ============================================
-- Store Media Table (Pictures)
-- ============================================
CREATE TABLE store_media (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    franchisee_id INTEGER REFERENCES franchisees(id) ON DELETE SET NULL,
    
    -- File information
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    
    -- Metadata
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER, -- user_id if user management is added
    description TEXT,
    is_primary BOOLEAN DEFAULT false,
    
    -- Ensure only one primary image per store
    UNIQUE(store_id) WHERE is_primary = true
);

CREATE INDEX idx_media_store ON store_media(store_id);
CREATE INDEX idx_media_franchisee ON store_media(franchisee_id) WHERE franchisee_id IS NOT NULL;
CREATE INDEX idx_media_uploaded_at ON store_media(uploaded_at DESC);

-- ============================================
-- API Keys Table (for API Key Authentication)
-- ============================================
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(255) NOT NULL UNIQUE, -- Hashed API key (bcrypt)
    name VARCHAR(255) NOT NULL,
    client_system VARCHAR(100), -- 'bi', 'erp', 'eorder', etc.
    
    -- Status
    active BOOLEAN DEFAULT true,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- Rate limiting (optional)
    rate_limit_per_minute INTEGER DEFAULT 60
);

CREATE INDEX idx_api_keys_active ON api_keys(active) WHERE active = true;
CREATE INDEX idx_api_keys_client ON api_keys(client_system) WHERE client_system IS NOT NULL;

-- ============================================
-- OAuth2 Clients Table
-- ============================================
CREATE TABLE oauth_clients (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL UNIQUE,
    client_secret_hash VARCHAR(255) NOT NULL, -- Hashed client secret (bcrypt)
    name VARCHAR(255) NOT NULL,
    redirect_uris TEXT[], -- Array of allowed redirect URIs
    
    -- Status
    active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_oauth_clients_active ON oauth_clients(active) WHERE active = true;

-- ============================================
-- OAuth2 Tokens Table
-- ============================================
CREATE TABLE oauth_tokens (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    access_token_hash VARCHAR(255) NOT NULL UNIQUE, -- Hashed access token
    refresh_token_hash VARCHAR(255) UNIQUE, -- Hashed refresh token
    
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scopes TEXT[] DEFAULT '{}' -- Array of permission scopes
);

CREATE INDEX idx_oauth_tokens_client ON oauth_tokens(client_id);
CREATE INDEX idx_oauth_tokens_expires ON oauth_tokens(expires_at);

-- ============================================
-- Trigger Functions for Updated At
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_stores_updated_at BEFORE UPDATE ON stores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_franchisees_updated_at BEFORE UPDATE ON franchisees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_store_schedules_updated_at BEFORE UPDATE ON store_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Helper Functions for Polygon Management
-- ============================================

-- Function to set previous versions as inactive when new current version is created
CREATE OR REPLACE FUNCTION set_previous_polygon_inactive()
RETURNS TRIGGER AS $$
BEGIN
    -- When a new polygon is marked as current, unmark previous current
    IF NEW.is_current = true AND NEW.inactive = false THEN
        UPDATE polygon_versions
        SET is_current = false
        WHERE store_id = NEW.store_id
          AND polygon_type = NEW.polygon_type
          AND id != NEW.id
          AND is_current = true;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER polygon_version_trigger BEFORE INSERT OR UPDATE ON polygon_versions
    FOR EACH ROW EXECUTE FUNCTION set_previous_polygon_inactive();

-- Function to validate polygon type consistency (dedicated should contain delivery)
-- This is a helper function that can be called from application code
CREATE OR REPLACE FUNCTION validate_polygon_hierarchy(store_id_param INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    dedicated_polygon GEOMETRY;
    delivery_polygon GEOMETRY;
BEGIN
    -- Get current dedicated area
    SELECT geometry INTO dedicated_polygon
    FROM polygon_versions
    WHERE store_id = store_id_param
      AND polygon_type = 'dedicated'
      AND is_current = true
      AND inactive = false
    LIMIT 1;
    
    -- Get current delivery area
    SELECT geometry INTO delivery_polygon
    FROM polygon_versions
    WHERE store_id = store_id_param
      AND polygon_type = 'delivery'
      AND is_current = true
      AND inactive = false
    LIMIT 1;
    
    -- If both exist, check if dedicated contains delivery
    IF dedicated_polygon IS NOT NULL AND delivery_polygon IS NOT NULL THEN
        RETURN ST_Contains(dedicated_polygon, delivery_polygon);
    END IF;
    
    -- If only one exists or neither exists, it's valid
    RETURN true;
END;
$$ language 'plpgsql';

-- ============================================
-- Views for Common Queries
-- ============================================

-- View: Current polygons for all stores
CREATE OR REPLACE VIEW current_polygons AS
SELECT 
    pv.id,
    pv.store_id,
    s.name AS store_name,
    pv.polygon_type,
    pv.geometry,
    pv.version_number,
    pv.created_at
FROM polygon_versions pv
JOIN stores s ON pv.store_id = s.id
WHERE pv.is_current = true 
  AND pv.inactive = false
  AND s.active = true;

-- View: Store details with current polygons
CREATE OR REPLACE VIEW store_details AS
SELECT 
    s.id,
    s.name,
    s.latitude,
    s.longitude,
    s.entersoft_key,
    s.inorder_key,
    s.future_proof_key,
    s.current_franchisee_id,
    f.name AS franchisee_name,
    s.active,
    s.created_at,
    s.updated_at,
    (SELECT geometry FROM polygon_versions 
     WHERE store_id = s.id AND polygon_type = 'dedicated' 
     AND is_current = true AND inactive = false 
     LIMIT 1) AS dedicated_area,
    (SELECT geometry FROM polygon_versions 
     WHERE store_id = s.id AND polygon_type = 'delivery' 
     AND is_current = true AND inactive = false 
     LIMIT 1) AS delivery_area
FROM stores s
LEFT JOIN franchisees f ON s.current_franchisee_id = f.id;

-- ============================================
-- Comments for Documentation
-- ============================================
COMMENT ON TABLE stores IS 'Store locations with external system keys';
COMMENT ON TABLE franchisees IS 'Franchisee/company information';
COMMENT ON TABLE polygon_versions IS 'Versioned polygons (dedicated and delivery areas) with PostGIS geometry';
COMMENT ON TABLE store_schedules IS 'Store operating hours per day of week with multiple time ranges';
COMMENT ON TABLE store_media IS 'Store pictures linked to franchisees with upload timestamps';
COMMENT ON TABLE api_keys IS 'API key authentication for external systems (BI, ERP, E-Order)';
COMMENT ON TABLE oauth_clients IS 'OAuth2 client credentials for authentication';
COMMENT ON TABLE oauth_tokens IS 'OAuth2 access and refresh tokens';

COMMENT ON COLUMN polygon_versions.polygon_type IS 'Type: dedicated (larger area) or delivery (smaller, usually contained in dedicated)';
COMMENT ON COLUMN polygon_versions.is_current IS 'Only one polygon per store+type should have is_current=true';
COMMENT ON COLUMN store_schedules.time_ranges IS 'JSONB array of time ranges: [{"start": "08:00", "end": "14:00"}]';
