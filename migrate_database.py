#!/usr/bin/env python3
"""
Database Schema Migration Script

Updates the database schema to support enhanced multi-session functionality.

Author: Traffic Simulator Team
Date: September 2025
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from database.models import Base
from database.service import DatabaseService
from sqlalchemy import create_engine

def migrate_database():
    """Migrate database schema to support enhanced session management"""
    print("=" * 60)
    print("Database Schema Migration")
    print("=" * 60)
    
    print("\n1. Backing up existing database...")
    import shutil
    from pathlib import Path
    
    db_path = Path("backend/traffic_simulator.db")
    if db_path.exists():
        backup_path = Path("backend/traffic_simulator_backup.db")
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
    else:
        print("✓ No existing database found, creating new one")
    
    print("\n2. Creating new database with updated schema...")
    
    # Remove old database
    if db_path.exists():
        db_path.unlink()
        print("✓ Old database removed")
    
    # Create new database with updated schema
    db_service = DatabaseService()
    print("✓ New database created with enhanced schema")
    
    print("\n3. Initializing networks from filesystem...")
    db_service.initialize_networks_from_filesystem("backend/networks")
    print("✓ Networks initialized in database")
    
    print("\n4. Testing new schema...")
    # Test creating a session with new fields
    test_session = db_service.create_session(
        session_id="test_migration_session",
        network_id="sm_molino_area",
        traci_port=8813,
        enable_gui=True,
        temp_directory="/tmp/test"
    )
    
    if test_session:
        print("✓ New schema working correctly")
        print(f"  - Session ID: {test_session.id}")
        print(f"  - TraCI Port: {test_session.traci_port}")
        print(f"  - Enable GUI: {test_session.enable_gui}")
        print(f"  - Is Active: {test_session.is_active}")
        
        # Clean up test session
        db_service.delete_session("test_migration_session")
        print("✓ Test session cleaned up")
    else:
        print("✗ Failed to create test session")
        return False
    
    print("\n" + "=" * 60)
    print("✓ DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    migrate_database()
