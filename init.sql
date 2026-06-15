-- =========================================================================
-- DDL SQL Script for AI Agent Office (Discord Bot Backed by PostgreSQL 16)
-- Designed by Senior Data Engineer & Solution Architect
-- Optimized for Big Data Scans, Dynamic Agent Updates, and Fast Queries
-- =========================================================================

-- 1. Create a trigger function to automatically update 'updated_at' column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Create Table: agent_knowledge (Brain / Persona / Dynamic Logic)
CREATE TABLE IF NOT EXISTS agent_knowledge (
    agent_id VARCHAR(50) PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    skill_set TEXT,
    context_data TEXT,
    learned_logic TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert Default Persona for Agent-001 (Project Manager)
INSERT INTO agent_knowledge (agent_id, agent_name, skill_set, context_data, learned_logic)
VALUES (
    'Agent-001', 
    'Agent-001 (Project Manager)', 
    'Acts as a Senior Project Manager / Business Analyst. Specializes in drafting software Requirement Specifications, clarifying scopes, and eliciting functional requirements.',
    'System Context: Discord Bot Client -> n8n Modular Workflows -> PostgreSQL Backend Database.',
    'Rule 1: Always respond professionally. Rule 2: If the user provides raw inputs, structure them into Markdown Specs. Rule 3: Support commands like /logic, /fix, /learn to update agent_knowledge dynamically.'
) ON CONFLICT (agent_id) DO UPDATE 
SET agent_name = EXCLUDED.agent_name,
    skill_set = EXCLUDED.skill_set,
    context_data = EXCLUDED.context_data,
    learned_logic = EXCLUDED.learned_logic;

-- Trigger for agent_knowledge to keep updated_at accurate
CREATE TRIGGER trg_update_agent_knowledge_updated_at
    BEFORE UPDATE ON agent_knowledge
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- 3. Create Table: chat_history (Session-based conversation logs)
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL, -- Managed by Discord Channel ID
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- DATA ENGINEERING OPTIMIZATION: Index on session_id for chat_history
-- Fast index scans for retrieving conversation history per session/channel (O(log N))
CREATE INDEX IF NOT EXISTS idx_chat_history_session_id 
ON chat_history (session_id);


-- 4. Create Table: project_specs (Requirement Specification Drafts)
CREATE TABLE IF NOT EXISTS project_specs (
    spec_id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL UNIQUE, -- UNIQUE constraint to support UPSERT (ON CONFLICT DO UPDATE)
    raw_input TEXT,
    formatted_spec TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- DATA ENGINEERING OPTIMIZATION: Index on session_id for project_specs
-- Although UNIQUE implicitly creates a unique index in PostgreSQL, 
-- we explicitly define it here to document and ensure strict indexing.
CREATE UNIQUE INDEX IF NOT EXISTS idx_project_specs_session_id 
ON project_specs (session_id);

-- Trigger for project_specs to keep updated_at accurate
CREATE TRIGGER trg_update_project_specs_updated_at
    BEFORE UPDATE ON project_specs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
