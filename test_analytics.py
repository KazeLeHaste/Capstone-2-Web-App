#!/usr/bin/env python3
"""
Test script to verify analytics functionality
"""

import json
import requests
from pathlib import Path

# Test the analytics sessions API
try:
    response = requests.get('http://localhost:5000/api/analytics/sessions')
    if response.status_code == 200:
        data = response.json()
        print("Analytics API Response:")
        print(json.dumps(data, indent=2))
        
        if data['success'] and data['sessions']:
            print(f"\nFound {len(data['sessions'])} sessions")
            for session in data['sessions'][:3]:  # Show first 3
                print(f"- {session['session_id']}: can_analyze={session['can_analyze']}, has_stats={session['has_stats']}")
        else:
            print("No analyzable sessions found")
    else:
        print(f"API Error: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"Error calling API: {e}")

# Test manually checking files in a recent session
sessions_dir = Path("backend/sessions")
if sessions_dir.exists():
    print(f"\nManually checking session files...")
    recent_sessions = sorted(sessions_dir.glob("session_*"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
    
    for session_dir in recent_sessions:
        print(f"\nSession: {session_dir.name}")
        
        tripinfo_files = list(session_dir.glob("*.tripinfos.xml"))
        stats_files = list(session_dir.glob("*.stats.xml"))
        metadata_file = session_dir / "session_metadata.json"
        
        print(f"  - Trip info files: {len(tripinfo_files)}")
        print(f"  - Stats files: {len(stats_files)}")
        print(f"  - Has metadata: {metadata_file.exists()}")
        print(f"  - Can analyze: {len(tripinfo_files) > 0 or len(stats_files) > 0}")
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                print(f"  - Metadata keys: {list(metadata.keys())}")
            except:
                print(f"  - Error reading metadata")
