# POS-AI Project Task Tracking

## Phase 1: Database & Backend API Development
- [x] Task 1.1: Initialize Backend Project
  - Setup Node.js TypeScript project, Express, Prisma ORM, and Supabase PostgreSQL connection
  - Configure ESLint, Prettier, and Vitest for testing
- [x] Task 1.2: Database Schema Design
  - Design Prisma Schema with models: `User` (roles: Owner, Manager, Cashier, Staff), `Category`, `Product`, `ProductOption`, `Table`, `Order`, `OrderItem`, `Transaction`, and `Inventory`
  - Generate Prisma migration and apply to Supabase database
- [x] Task 1.3: Authentication & Authorization API
  - Implement Login and Token validation endpoints
  - Implement role-based access control (RBAC) middleware (Owner, Manager, Cashier, Staff)
  - **Unit Test**: Test authentication logic, JWT generation, password hashing, and role verification
- [x] Task 1.4: Menu & Category API
  - Implement CRUD APIs for categories and products (with optional customization like sweetness level, extra toppings)
  - Integrate image upload logic for products
  - **Unit Test**: Validate category/product schema payloads and authorization checks
- [x] Task 1.5: Table Management API
  - Implement CRUD APIs for tables and their status tracking (vacant, occupied, billing)
- [x] Task 1.6: Order & Billing API
  - Implement Create Order, Add Items to Order, Update Order Status (Pending, Preparing, Served, Billing, Paid)
  - Implement checkout/payment API (supports cash, QR code mock, calculating discounts, taxes, and change)
  - **Unit Test**: Test billing logic, including total computation with options, tax/service charge, discounts, and validation of payment inputs
- [x] Task 1.7: Inventory/Stock Management API
  - Implement stock deduction logic upon checkout
  - Implement CRUD APIs for raw stock/inventory items and manual adjustments
  - **Unit Test**: Test concurrent stock deduction and low stock warning triggers
- [x] Task 1.8: Analytics & Report API (for Manager App)
  - Implement dashboard endpoints for daily/weekly/monthly sales, top-selling products, and order statistics

---

## Phase 2: POS Front-End App (Staff/Cashier) - Flutter
- [x] Task 2.1: Initialize Flutter POS App Project
  - Create Flutter project structure, configure routers (go_router), and setup state management (e.g., Riverpod or Provider)
- [x] Task 2.2: API Service & Authentication Flow
  - Create HTTP/Dio API client with interceptors for JWT token attachment and error handling
  - Build Login Screen and persist session tokens securely
- [x] Task 2.3: Table Selection Layout
  - Build a visual grid interface displaying table layouts and statuses (occupied, vacant, pending bill)
- [x] Task 2.4: Menu Catalog & Ordering Interface
  - Build menu page with Category tabs
  - Build Product card grid/list
  - Build Product Option Modal (popup sheet to select sweetness, size, extra toppings)
- [x] Task 2.5: Cart & Order Management
  - Build cart sidebar/screen showing added items, calculations (subtotal, tax, discounts, total)
  - Add option to write notes/instructions for specific items (e.g. "no onion")
  - **Unit Test**: Test Cart state notifier (adding, updating quantities, clearing, and calculating prices/taxes)
- [x] Task 2.6: Billing & Checkout Interface
  - Build checkout sheet showing summary of order
  - Build payment dialogue with quick cash buttons (e.g., $100, $500, $1000) and change calculator
  - Build QR code payment mock screen
- [x] Task 2.7: Order Status Tracker (Kitchen/Server view)
  - Build a simplified kitchen view displaying active orders to prepare and update status (Preparing -> Ready -> Served)
- [x] Task 2.8: UI/Integration Tests
  - Implement Widget tests for the order cart and checkout flow validation

---

## Phase 3: POS Manager App (Owner/Manager) - Flutter
- [x] Task 3.1: Initialize Flutter Manager App Project
  - Create Flutter project structure, router config, and state management
- [x] Task 3.2: Dashboard & Reports UI
  - Design dashboard homepage with interactive charts (e.g., fl_chart) showing sales graphs, total revenue, and order volume
  - Add filtering options (by day, week, month, branch)
  - Display top-selling items and categories
- [x] Task 3.3: Menu & Category Management (CRUD)
  - Build Category editor (CRUD)
  - Build Product catalog editor (Create, Read, Update, Delete menu items, prices, options, and status)
- [x] Task 3.4: Table Management Setup
  - Build interface to add, remove, and rename physical tables
- [x] Task 3.5: Inventory & Stock Tracking UI
  - Build screen to monitor ingredient/product stock levels
  - Highlight low stock alerts
  - Enable stock level adjustments/adjustment form
- [x] Task 3.6: Employee Management
  - Build interface to manage staff members, create credentials, and assign roles (Cashier, Staff, Manager)
- [x] Task 3.7: UI/Integration Tests
  - Implement Widget/Unit tests for dashboard filter logic and menu creation validation

---

## Phase 4: POS-Raykha AI Chat App
### Backend & Agent Development (Python FastAPI)
- [x] Task 4.1: Project Setup & Central DB Integration
  - Initialize python FastAPI project in `/home/krit/my-office/pos-ai/pos_raykha_backend` and configure connection to the central PostgreSQL database
- [x] Task 4.2: Tenant Metadata & Dynamic Connection Pooler
  - Define schema for Tenant registry and implement dynamically routed DB connection pools based on user tenant context
- [x] Task 4.3: Hermes Filter & Prompts Enrichment
  - Implement `HermesService` to filter inbound text, inject system instructions (Persona: Raykha), and sanitize outbound responses
- [x] Task 4.4: DB-Agent & Tenant-Isolated SQL Query Generator
  - Build AI service instructing Typhoon/Gemini to write read-only PostgreSQL queries executed strictly on the isolated tenant database
- [x] Task 4.5: Chat API Endpoints Assembly
  - Expose API endpoints for managing chat sessions, listing past chats, and posting messages to the AI Agent

### Flutter Application (pos_raykha_app)
- [x] Task 4.6: Project Initialization
  - Initialize Flutter project `pos_raykha_app` under `/home/krit/my-office/pos-ai/pos_raykha_app` with router and state provider
- [x] Task 4.7: Speech-to-Text (STT) voice input
  - Integrate speech recognition capabilities to dictate text messages using native OS voice systems
- [x] Task 4.8: Chat Sessions Sidebar & Snippets
  - Build sidebar listing previous chat histories showing snippets and a "New Chat" button
- [x] Task 4.9: Chat UI & Voice Feedback
  - Design premium chat screens, recording status animations, and Text-to-Speech response reading

