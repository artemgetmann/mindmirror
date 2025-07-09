#!/usr/bin/env python3
"""
Test Supabase PostgreSQL connection
"""
import psycopg2
import psycopg2.extras
import secrets

# Database configuration
DB_CONFIG = {
    'host': 'REDACTED_SUPABASE_PROJECT_ID.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'REDACTED_DB_PASSWORD',
    'port': 5432
}

def test_connection():
    """Test PostgreSQL connection and basic operations"""
    try:
        print("🔗 Testing Supabase PostgreSQL connection...")
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("✅ Connection successful!")
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"📋 PostgreSQL version: {version}")
        
        # Create test table
        print("🏗️  Creating auth_tokens table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_tokens (
                id SERIAL PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT true
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_token ON auth_tokens(token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_active ON auth_tokens(is_active)")
        
        print("✅ Table and indexes created successfully!")
        
        # Test insert
        test_token = secrets.token_urlsafe(32)
        cursor.execute("""
            INSERT INTO auth_tokens (token, user_id, user_name) 
            VALUES (%s, %s, %s)
        """, (test_token, "test_user", "Test User"))
        
        print("✅ Insert successful!")
        
        # Test select
        cursor.execute("SELECT COUNT(*) FROM auth_tokens WHERE is_active = true")
        count = cursor.fetchone()[0]
        print(f"📊 Active tokens count: {count}")
        
        # Test update
        cursor.execute("""
            UPDATE auth_tokens 
            SET last_used = CURRENT_TIMESTAMP 
            WHERE token = %s
        """, (test_token,))
        
        print("✅ Update successful!")
        
        # Test select with token
        cursor.execute("""
            SELECT user_id FROM auth_tokens 
            WHERE token = %s AND is_active = true
        """, (test_token,))
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Token lookup successful: {result[0]}")
        
        # Commit changes
        conn.commit()
        
        print("🎉 All database operations successful!")
        print(f"🔑 Test token created: {test_token}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\n🚀 Ready to deploy with Supabase!")
    else:
        print("\n💥 Fix connection issues before deployment")