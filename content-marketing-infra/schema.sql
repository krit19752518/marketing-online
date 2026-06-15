-- ==========================================
-- SQL DDL Schema for Content Marketing System
-- Designed for High Scalability & Performance
-- ==========================================

-- Enable UUID generation extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Table: marketing_content (Stores content ideas, generations, and processing status)
CREATE TABLE IF NOT EXISTS marketing_content (
    content_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_idea TEXT NOT NULL,
    generated_caption TEXT, -- Structured for AIDA (Attention, Interest, Desire, Action)
    media_urls JSONB DEFAULT '[]'::jsonb, -- JSONB stores array of media links from Cloud Storage
    status VARCHAR(50) NOT NULL DEFAULT 'pending_ai' 
        CONSTRAINT chk_status CHECK (status IN ('pending_ai', 'generated', 'pending_approval', 'approved', 'rejected', 'published')),
    target_platform VARCHAR(100) NOT NULL, -- e.g., 'facebook', 'tiktok', 'instagram'
    batch_id UUID NOT NULL, -- Group identifier for Batch Processing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table: content_approval_logs (Audit logs for human-in-the-loop review via Telegram/Web portals)
CREATE TABLE IF NOT EXISTS content_approval_logs (
    log_id SERIAL PRIMARY KEY,
    content_id UUID NOT NULL REFERENCES marketing_content(content_id) ON DELETE CASCADE,
    telegram_chat_id BIGINT NOT NULL,
    telegram_message_id BIGINT NOT NULL, -- Used to track and update the inline keyboard buttons asynchronously
    reviewer_feedback TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- Big Data Query Optimization & Indexing
-- ==========================================

-- Index on 'status'
-- Why: Frequently queried by n8n workflow workers (e.g., pulling 'pending_ai' or 'approved' items).
CREATE INDEX IF NOT EXISTS idx_marketing_content_status 
ON marketing_content(status);

-- Index on 'batch_id'
-- Why: Essential for batch operations, reporting, and grouping tasks during automated processing.
CREATE INDEX IF NOT EXISTS idx_marketing_content_batch_id 
ON marketing_content(batch_id);

-- Composite Index on 'created_at' and 'status'
-- Why: Optimizes time-series retrieval, such as finding the latest 'pending_ai' contents for processing.
CREATE INDEX IF NOT EXISTS idx_marketing_content_created_status 
ON marketing_content(created_at DESC, status);

-- Trigger to auto-update 'updated_at' column
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_marketing_content_modtime
    BEFORE UPDATE ON marketing_content
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();


-- ==========================================
-- AI Brain & Spec Generator Schema
-- ==========================================

-- 1. Table: project_specs (Stores Requirement Specs draft/finalized by Agent-001)
CREATE TABLE IF NOT EXISTS project_specs (
    spec_id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,       -- Chat room session ID (Unique per session)
    raw_input TEXT,                         -- Raw requirements from user
    formatted_spec TEXT,                    -- Formatted spec document
    status VARCHAR(50) DEFAULT 'draft'
        CONSTRAINT chk_spec_status CHECK (status IN ('draft', 'finalized')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table: chat_history (Stores chat logs for routers/context engines)
CREATE TABLE IF NOT EXISTS chat_history (
    chat_id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,       -- Chat room session ID
    role VARCHAR(50) NOT NULL,              -- e.g., 'user', 'assistant'
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index on 'session_id' for project_specs
CREATE INDEX IF NOT EXISTS idx_specs_session ON project_specs(session_id);

-- Index on 'session_id' for chat_history
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);

-- Trigger to auto-update 'updated_at' column on project_specs
CREATE OR REPLACE TRIGGER update_project_specs_modtime
    BEFORE UPDATE ON project_specs
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();


-- 3. Table: agent_knowledge (Stores skills, context, and learned logic for AI Agents)
CREATE TABLE IF NOT EXISTS agent_knowledge (
    agent_id VARCHAR(50) PRIMARY KEY,
    skill_set TEXT,
    context_data TEXT,
    learned_logic TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed default knowledge for Agent-001
INSERT INTO agent_knowledge (agent_id, skill_set, context_data, learned_logic)
VALUES (
    'Agent-001', 
    'AIDA Model Content Writing, Technical Spec Generation', 
    'Content Marketing Platform Infrastructure v1.0', 
    'Default instruction set: reply politely and structure responses clearly.'
)
ON CONFLICT (agent_id) DO NOTHING;


