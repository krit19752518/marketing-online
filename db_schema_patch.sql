-- SQL Patch to add bot action tracking and API failover status tables

-- 1. Create enum/check status constraints
CREATE TABLE IF NOT EXISTS bot_action_logs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL, -- Discord Channel/DM ID
    sender_id VARCHAR(100) NOT NULL,  -- Discord User ID who sent the message
    receiver_bot_id VARCHAR(50) NOT NULL, -- The bot role ID that received the DM (e.g. 'MD', 'PM', 'SA', etc.)
    message_content TEXT NOT NULL,
    routed_target_bot_id VARCHAR(50), -- If routed, which bot should handle next (e.g. 'Programmer-001')
    status VARCHAR(50) NOT NULL DEFAULT 'pending_approval' 
        CHECK (status IN ('pending_approval', 'approved', 'sent', 'out_of_scope', 'failed')),
    revised_content TEXT, -- Content edited by user before approving
    token_usage INT,
    provider_used VARCHAR(50) DEFAULT 'openrouter',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index on session_id and status for faster dashboard queries
CREATE INDEX IF NOT EXISTS idx_bot_action_logs_session_id ON bot_action_logs (session_id);
CREATE INDEX IF NOT EXISTS idx_bot_action_logs_status ON bot_action_logs (status);

-- 2. Create Table: api_limit_status (Tracks OpenRouter / LLM providers state)
CREATE TABLE IF NOT EXISTS api_limit_status (
    provider_name VARCHAR(50) PRIMARY KEY, -- e.g. 'openrouter', 'ollama', 'gemini'
    is_limited BOOLEAN DEFAULT FALSE,
    last_error TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial values for LLM providers
INSERT INTO api_limit_status (provider_name, is_limited)
VALUES 
    ('openrouter', FALSE),
    ('ollama', FALSE)
ON CONFLICT (provider_name) DO NOTHING;

-- Trigger to automatically update updated_at on both tables
CREATE TRIGGER trg_update_bot_action_logs_updated_at
    BEFORE UPDATE ON bot_action_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_update_api_limit_status_updated_at
    BEFORE UPDATE ON api_limit_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
