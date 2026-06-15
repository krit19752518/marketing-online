-- Migration: add category column to shopee_affiliate_cards table
ALTER TABLE shopee_affiliate_cards ADD COLUMN category TEXT DEFAULT 'หมวดหมู่อื่นๆ';
