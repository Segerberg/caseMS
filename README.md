# Ärendehanteringssystem (Case Management System)

A simple case management system for educational purposes demonstrating the integration of databases, frontend interfaces, and business logic layers.

## Educational Purpose

This system is designed specifically for educational contexts to:

1. Demonstrate how to build a multi-layer application with:
   - Database layer (SQLITE with raw SQL and ORM)
   - Business logic layer 
   - Presentation layer 

2. Provide practical examples of:
   - Database design and normalization
   - SQL query writing 
   - Web application architecture
   - Authentication and authorization

3. Serve as the basis for laboratory exercises in digital preservation where students:
   - Analyze the system's archival requirements
   - Develop strategies for preserving the system's data and structure
   - Implement solutions for long-term digital preservation
   - Practice migrating data between different formats and systems

## Features

- User authentication (login)
- Case management (create, view, edit)
- Case notes
- Activity logging
- Raw SQL queries for educational purposes
- JSON API endpoints

## API Endpoints

The system provides the following API endpoints:

- `GET /api/cases` - Returns a list of all cases in JSON format
- `GET /api/case/<dnr>` - Returns detailed information about a specific case by its DNR (case number)

All API endpoints require authentication and return JSON-formatted data.

## Database Structure

The system uses the following database tables:

- REG - Registry table
- DOSSIEPLAN - Case categories/dossiers
- HANDLAEGGARE - Case handlers/workers
- ENHET - Units/departments
- AERENDE - Cases
- AERENDE_ANT - Case notes
- LOG - Activity logs

## Installation and Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd caseMS
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Access the application at http://localhost:5000

6. Set up an admin account by visiting http://localhost:5000/auth/setup

## Educational Notes

This project is intentionally designed with certain educational patterns:

- Uses raw SQL queries for most database operations to demonstrate SQL usage and provide transparency into database operations
- Only the User model uses SQLAlchemy, allowing for comparison between ORM and raw SQL approaches
- Implements a simple API to demonstrate integration capabilities


## Archiving Exercises

The system includes features that make it suitable for laboratory exercises in digital preservation:

- Database structure that presents typical archiving challenges
- Sample data representing different types of case information

Students can use this system to practice:
- Data extraction and transformation
- Long-term preservation strategies
- Metadata management
