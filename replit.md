# Pavan's Bawarchi - Food Ordering System

## Overview

This is a comprehensive Flask-based web application for Pavan's Bawarchi restaurant featuring user authentication, AI-powered food recommendations, and a complete ordering system. The application uses a dark theme with gold accents and includes modern features like real-time chat assistance and responsive design.

## System Architecture

The application follows a modern full-stack architecture with the following components:

- **Backend**: Flask web framework with SQLAlchemy ORM and Flask-Login for authentication
- **Frontend**: Server-side rendered HTML templates with Bootstrap 5 and custom dark theme styling
- **Database**: PostgreSQL for production with SQLite fallback for development
- **AI Integration**: Google Gemini AI for intelligent food recommendations
- **Authentication**: Complete user registration and login system with session management
- **Real-time Features**: AI-powered chatbot for food suggestions

## Key Components

### Backend Components

1. **Flask Application (`app.py`)**
   - Main application entry point
   - Database configuration and initialization
   - Route definitions for menu display
   - Static menu data definition (10 food items)

2. **Database Models (`models.py`)**
   - `Order` model: Stores order metadata (ID, total amount, date)
   - `OrderItem` model: Stores individual items within orders
   - One-to-many relationship between Orders and OrderItems

3. **Application Entry Point (`main.py`)**
   - Simple Flask app runner for development
   - Configured for host='0.0.0.0' and port=5000

### Frontend Components

1. **Templates**
   - `base.html`: Base template with navigation and Bootstrap setup
   - `menu.html`: Menu display with item selection functionality
   - `orders.html`: Order history display (incomplete implementation)

2. **Static Assets**
   - `style.css`: Custom styling with CSS variables and hover effects
   - `menu.js`: Client-side functionality for real-time order management (incomplete)

## Data Flow

1. **Menu Display**: Static menu data is passed from Flask routes to templates
2. **Order Processing**: Form submissions capture selected items and quantities
3. **Database Storage**: Orders and order items are persisted using SQLAlchemy models
4. **Order History**: Past orders are retrieved and displayed with formatted timestamps

## External Dependencies

### Python Packages
- **Flask**: Web framework for request handling and templating
- **Flask-SQLAlchemy**: Database ORM integration
- **Werkzeug**: WSGI utilities including ProxyFix middleware

### Frontend Libraries (CDN-based)
- **Bootstrap 5**: UI framework for responsive design
- **Font Awesome 6**: Icon library for enhanced visual elements

## Deployment Strategy

The application is configured for flexible deployment:

- **Environment Variables**: 
  - `SESSION_SECRET`: Flask session security key
  - `DATABASE_URL`: Database connection string (defaults to SQLite)
- **WSGI Configuration**: ProxyFix middleware for reverse proxy compatibility
- **Database Settings**: Connection pooling and health checks configured
- **Development Mode**: Debug mode enabled with auto-reload functionality

## Technical Decisions

### Database Choice
- **Problem**: Need for persistent data storage
- **Solution**: SQLAlchemy with SQLite default
- **Rationale**: Simple setup for development, easily configurable for production databases
- **Pros**: No external dependencies, easy to set up
- **Cons**: Limited concurrent access, not suitable for production scale

### Frontend Architecture
- **Problem**: Need for responsive, interactive user interface
- **Solution**: Server-side rendering with Bootstrap and progressive enhancement via JavaScript
- **Rationale**: Simpler deployment, better SEO, graceful degradation
- **Pros**: Fast initial load, accessible, works without JavaScript
- **Cons**: Less dynamic, requires page refreshes for some interactions

### Static Menu Data
- **Problem**: Need for menu item information
- **Solution**: Hardcoded menu items in Python code
- **Rationale**: Simple implementation for prototype/demo
- **Pros**: No additional database complexity
- **Cons**: Not easily updatable, not scalable for real restaurant use

## Current Implementation Status

### Completed Features
- Menu display with item cards
- Basic order model structure
- Responsive navigation
- Bootstrap styling integration

### Incomplete Features
- Order placement functionality (route missing)
- Order history display (route missing)
- JavaScript interactivity for real-time price calculation
- Database table creation and initialization

## Recent Changes & Completed Features

### Latest Update - July 08, 2025
✅ **Menu Expansion**: Added 33+ authentic Hyderabadi dishes with unique, high-quality images
✅ **Enhanced Chatbot**: Ultra-prominent 80px glowing button with rotating border animation and "Ask Chef Pavan!" label
✅ **AI Personality**: Chef Pavan asks about your mood first, then suggests dishes accordingly
✅ **Visual Design**: Added spice-pattern backgrounds and biryani-themed sections
✅ **All Functionality Working**: Registration, login, order placement, history tracking, and AI chatbot

### Food Categories Added:
- **Biryanis**: 5 varieties (Chicken, Mutton, Fish, Prawn, Vegetable)
- **Non-Veg Classics**: Mutton Marag, Chicken Haleem, Keema Kaleji, Chicken Korma
- **Kebabs & Tandoor**: Seekh, Shammi, Boti Kebabs, Chicken/Fish Tikka
- **Vegetarian**: Paneer specialties, Dal Hyderabadi, Bagara Baingan
- **Breads & Rice**: Roomali Roti, Naan, Kulcha, Pulao
- **Desserts**: Double Ka Meetha, Khubani Ka Meetha, Kulfi Falooda, Gulab Jamun
- **Beverages**: Hyderabadi Chai, Lassi, Fresh Lime Water

### Technical Achievements:
- 100% unique food images (no duplicates)
- Mood-based AI food recommendations
- Animated, highly visible chatbot interface
- Professional Hyderabadi restaurant branding
- Complete order management system

## User Preferences

Preferred communication style: Simple, everyday language.