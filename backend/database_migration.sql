-- MYELIN Custom Rules Database Schema
-- Supabase Migration Script
-- Version: 1.0.0

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ORGANIZATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    tier VARCHAR(50) DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'enterprise')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_organizations_name ON organizations(name);
CREATE INDEX idx_organizations_tier ON organizations(tier);

-- ============================================================================
-- USERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'developer' CHECK (role IN ('admin', 'developer', 'viewer')),
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token_hash VARCHAR(255),
    email_verification_expires_at TIMESTAMP WITH TIME ZONE,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_email_verification_token_hash ON users(email_verification_token_hash);

-- Backward-compatible column additions for existing deployments
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP WITH TIME ZONE;

-- ============================================================================
-- API KEYS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    rate_limit_per_minute INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_organization_id ON api_keys(organization_id);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- ============================================================================
-- CUSTOM RULES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS custom_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    rule_id VARCHAR(50) NOT NULL,
    pillar VARCHAR(50) NOT NULL CHECK (pillar IN ('toxicity', 'governance', 'bias', 'factual', 'fairness')),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    severity VARCHAR(50) DEFAULT 'MEDIUM' CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    weight FLOAT DEFAULT 1.0 CHECK (weight >= 0 AND weight <= 10),
    rule_type VARCHAR(50) DEFAULT 'keyword' CHECK (rule_type IN ('keyword', 'regex', 'llm', 'custom')),
    rule_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, rule_id)
);

CREATE INDEX idx_custom_rules_organization_id ON custom_rules(organization_id);
CREATE INDEX idx_custom_rules_pillar ON custom_rules(pillar);
CREATE INDEX idx_custom_rules_is_active ON custom_rules(is_active);
CREATE INDEX idx_custom_rules_rule_type ON custom_rules(rule_type);

-- ============================================================================
-- AUDIT LOGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    audit_type VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    triggered_rules JSONB DEFAULT '[]'::jsonb,
    overall_decision VARCHAR(50),
    risk_level VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_api_key_id ON audit_logs(api_key_id);
CREATE INDEX idx_audit_logs_audit_type ON audit_logs(audit_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_overall_decision ON audit_logs(overall_decision);

-- ============================================================================
-- RULE TEMPLATES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS rule_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    pillar VARCHAR(50) NOT NULL CHECK (pillar IN ('toxicity', 'governance', 'bias', 'factual', 'fairness')),
    category VARCHAR(100),
    rule_type VARCHAR(50) CHECK (rule_type IN ('keyword', 'regex', 'llm', 'custom')),
    template_config JSONB NOT NULL,
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_rule_templates_pillar ON rule_templates(pillar);
CREATE INDEX idx_rule_templates_is_public ON rule_templates(is_public);

-- ============================================================================
-- SEED DATA - Rule Templates
-- ============================================================================

INSERT INTO rule_templates (name, description, pillar, category, rule_type, template_config) VALUES
('No Competitor Mentions', 'Detects mentions of competitor names', 'governance', 'Brand Protection', 'keyword', 
 '{"keywords": ["competitor1", "competitor2"], "case_sensitive": false, "whole_word_only": true}'::jsonb),

('No Medical Advice', 'Prevents providing medical advice', 'governance', 'Compliance', 'keyword',
 '{"keywords": ["diagnose", "prescribe", "medical advice", "treatment for"], "case_sensitive": false}'::jsonb),

('No Political Content', 'Blocks political discussions', 'governance', 'Content Policy', 'keyword',
 '{"keywords": ["election", "political party", "vote for"], "case_sensitive": false}'::jsonb),

('Email Pattern Detection', 'Detects email addresses in responses', 'governance', 'PII Protection', 'regex',
 '{"patterns": ["[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"], "flags": "i"}'::jsonb),

('Phone Number Detection', 'Detects phone numbers in responses', 'governance', 'PII Protection', 'regex',
 '{"patterns": ["\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b"], "flags": ""}'::jsonb),

('Profanity Filter', 'Custom profanity detection', 'toxicity', 'Language Filter', 'keyword',
 '{"keywords": ["badword1", "badword2"], "case_sensitive": false}'::jsonb),

('Gender Bias Keywords', 'Detects gender-biased language', 'bias', 'Gender Bias', 'keyword',
 '{"keywords": ["for a woman", "for a man", "like a girl"], "case_sensitive": false}'::jsonb);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_custom_rules_updated_at BEFORE UPDATE ON custom_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (Optional - for Supabase)
-- ============================================================================

-- Enable RLS on tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Note: Add specific RLS policies based on your security requirements
-- Example: Users can only see their own organization's data

-- ============================================================================
-- GRANTS (Adjust based on your Supabase setup)
-- ============================================================================

-- Grant permissions to authenticated users
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tables created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Verify indexes
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'public';

-- Check rule templates
-- SELECT name, pillar, rule_type FROM rule_templates;

-- ============================================================================
-- PERFORMANCE / SCALABILITY INDEXES
-- ============================================================================

-- Partial index for fast query of only active rules
CREATE INDEX IF NOT EXISTS idx_custom_rules_active ON custom_rules(organization_id, pillar) WHERE is_active = true;

-- Compound indexes to speed up the dashboard rendering for audit logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_composite ON audit_logs(organization_id, audit_type, created_at DESC);

-- Accelerate API Key verification
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(key_hash) WHERE is_active = true;

