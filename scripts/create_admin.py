#!/usr/bin/env python3
"""
Create admin user script
"""
import sys
import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Add parent directory to path
sys.path.insert(0, '/opt/proxmox-cronjob/backend')

from app.models import User
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_admin_user():
    """Create or update admin user"""
    print("Create Admin User")
    print("=" * 50)
    
    username = input("Username [admin]: ").strip() or "admin"
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm Password: ")
    
    if password != password_confirm:
        print("❌ Passwords do not match!")
        return
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if user exists
        user = session.query(User).filter(User.username == username).first()
        
        if user:
            # Update existing user
            user.password_hash = pwd_context.hash(password)
            print(f"✅ Updated password for user '{username}'")
        else:
            # Create new user
            user = User(
                username=username,
                password_hash=pwd_context.hash(password)
            )
            session.add(user)
            print(f"✅ Created new user '{username}'")
        
        session.commit()
        print("\nUser created/updated successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {str(e)}")
    finally:
        session.close()


if __name__ == "__main__":
    create_admin_user()
