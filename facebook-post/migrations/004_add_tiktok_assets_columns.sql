-- Migration: add background and final slide image paths for TikTok Flow
ALTER TABLE shopee_affiliate_cards ADD COLUMN slide1_bg_path TEXT;
ALTER TABLE shopee_affiliate_cards ADD COLUMN slide2_bg_path TEXT;
ALTER TABLE shopee_affiliate_cards ADD COLUMN slide3_bg_path TEXT;
ALTER TABLE shopee_affiliate_cards ADD COLUMN slide1_final_path TEXT;
ALTER TABLE shopee_affiliate_cards ADD COLUMN slide2_final_path TEXT;
ALTER TABLE shopee_affiliate_cards ADD COLUMN slide3_final_path TEXT;
