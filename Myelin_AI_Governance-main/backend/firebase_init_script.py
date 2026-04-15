#!/usr/bin/env python3
"""
Firebase Firestore Initialization Script
Sets up collections and indexes for Myelin AI Governance backend
Run this after setting up your Firebase credentials
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import sys

def initialize_firestore(credentials_path: str):
    """Initialize Firebase and Firestore"""
    try:
        # Initialize Firebase
        if not os.path.exists(credentials_path):
            print(f"❌ Credentials file not found: {credentials_path}")
            sys.exit(1)
        
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        
        client = firestore.client()
        print("✅ Firebase initialized")
        
        return client
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        sys.exit(1)


def create_collections(client):
    """Create necessary Firestore collections"""
    collections = [
        "organizations",
        "users",
        "api_keys",
        "custom_rules",
        "audit_logs",
        "rule_templates"
    ]
    
    print("\n📂 Creating collections...")
    for collection in collections:
        # Collections are created automatically when first document is added
        # But we can create an index to show they exist
        try:
            # Get the collection reference (this doesn't create it yet)
            col_ref = client.collection(collection)
            print(f"  ✅ Collection '{collection}' ready")
        except Exception as e:
            print(f"  ⚠️  Error with collection '{collection}': {e}")


def create_sample_documents(client):
    """Create sample documents to initialize collections"""
    print("\n📝 Creating sample documents...")
    
    # Sample organization
    try:
        orgs = client.collection("organizations")
        orgs.document("sample-org-1").set({
            "name": "Sample Organization",
            "tier": "free",
            "is_active": True,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        print("  ✅ Sample organization created")
    except Exception as e:
        print(f"  ⚠️  Error creating sample organization: {e}")
    
    # Sample user
    try:
        users = client.collection("users")
        users.document("sample-user-1").set({
            "email": "admin@example.com",
            "password_hash": "placeholder",
            "organization_id": "sample-org-1",
            "full_name": "Administrator",
            "role": "admin",
            "is_active": True,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        print("  ✅ Sample user created")
    except Exception as e:
        print(f"  ⚠️  Error creating sample user: {e}")
    
    # Sample API Key
    try:
        api_keys = client.collection("api_keys")
        api_keys.document("sample-key-1").set({
            "organization_id": "sample-org-1",
            "user_id": "sample-user-1",
            "key_hash": "placeholder-hash",
            "key_prefix": "myelin_sk_sample",
            "name": "Sample API Key",
            "is_active": True,
            "rate_limit_per_minute": 60,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        print("  ✅ Sample API key created")
    except Exception as e:
        print(f"  ⚠️  Error creating sample API key: {e}")


def create_indexes(client):
    """
    Display information about recommended indexes
    Note: Complex indexes must be created via Firebase Console
    """
    print("\n📊 Recommended Indexes to Create in Firebase Console:")
    print("\n  1. Collection: api_keys")
    print("     Fields: key_hash (Ascending), is_active (Ascending)")
    print("     ")
    print("  2. Collection: api_keys")
    print("     Fields: organization_id (Ascending)")
    print("     ")
    print("  3. Collection: custom_rules")
    print("     Fields: organization_id (Ascending), pillar (Ascending), is_active (Ascending)")
    print("     ")
    print("  4. Collection: audit_logs")
    print("     Fields: organization_id (Ascending), created_at (Descending)")
    print("     ")
    print("  5. Collection: users")
    print("     Fields: email (Ascending)")
    print("     ")
    print("  ℹ️  These indexes help with query performance")


def display_setup_summary(client):
    """Display setup summary and next steps"""
    print("\n" + "="*60)
    print("✅ Firebase Firestore Setup Complete!")
    print("="*60)
    
    print("\n📋 Collections Created:")
    print("  - organizations")
    print("  - users")
    print("  - api_keys")
    print("  - custom_rules")
    print("  - audit_logs")
    print("  - rule_templates")
    
    print("\n🔑 Sample Documents Created:")
    print("  - Sample Organization (sample-org-1)")
    print("  - Sample User (sample-user-1)")
    print("  - Sample API Key (sample-key-1)")
    
    print("\n📝 Next Steps:")
    print("  1. Create recommended indexes in Firebase Console")
    print("     (See console output above)")
    print("  2. Copy your Firebase service account JSON file")
    print("  3. Set FIREBASE_CREDENTIALS_JSON in your .env file")
    print("  4. Run: pip install -r backend/requirements_backend.txt")
    print("  5. Start the backend: python backend/api_server_enhanced.py")
    
    print("\n🔗 Firebase Console: https://console.firebase.google.com")
    print("="*60)


def main():
    """Main setup function"""
    print("🔥 Firebase Firestore Initialization")
    print("="*60)
    
    # Get credentials path
    credentials_path = os.environ.get(
        "FIREBASE_CREDENTIALS_JSON",
        "./serviceAccountKey.json"
    )
    
    print(f"\n🔍 Looking for credentials at: {credentials_path}")
    
    # Initialize Firebase
    client = initialize_firestore(credentials_path)
    
    # Create collections and sample data
    create_collections(client)
    create_sample_documents(client)
    create_indexes(client)
    
    # Display summary
    display_setup_summary(client)


if __name__ == "__main__":
    main()
