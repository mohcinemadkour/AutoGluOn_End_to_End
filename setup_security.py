"""
Security Setup Script
=====================
Quick setup script for authentication and security features
"""

import os
import secrets
from pathlib import Path

def generate_secret_key():
    """Generate a secure random secret key"""
    return secrets.token_hex(32)

def create_env_file():
    """Create .env file from template"""
    env_example = Path('.env.example')
    env_file = Path('.env')
    
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Skipping .env creation")
            return
    
    if not env_example.exists():
        print("Error: .env.example not found!")
        return
    
    # Read template
    with open(env_example, 'r') as f:
        content = f.read()
    
    # Generate new secret keys
    jwt_secret = generate_secret_key()
    session_secret = generate_secret_key()
    
    # Replace placeholders
    content = content.replace(
        'your-super-secret-key-change-this-in-production-use-openssl-rand-hex-32',
        jwt_secret
    )
    content = content.replace(
        'another-secret-key-for-sessions',
        session_secret
    )
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Created .env file with secure secret keys")
    print(f"   JWT Secret: {jwt_secret[:20]}...")
    print(f"   Session Secret: {session_secret[:20]}...")

def create_log_directories():
    """Create necessary log directories"""
    log_dirs = [
        'logs/audit',
        'logs/app'
    ]
    
    for log_dir in log_dirs:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {log_dir}")

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi',
        'streamlit',
        'jwt',
        'passlib',
        'slowapi',
        'python_jose',
        'bcrypt',
        'dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("⚠️  Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed")
        return True

def display_default_credentials():
    """Display default user credentials"""
    print("\n" + "="*60)
    print("DEFAULT USER CREDENTIALS (FOR DEMO ONLY)")
    print("="*60)
    print("\n⚠️  CHANGE THESE IN PRODUCTION! ⚠️\n")
    print("Admin Account:")
    print("  Username: admin")
    print("  Password: admin123")
    print("  Role: Full access")
    print()
    print("Analyst Account:")
    print("  Username: analyst")
    print("  Password: analyst123")
    print("  Role: Analysis & predictions")
    print()
    print("Viewer Account:")
    print("  Username: viewer")
    print("  Password: viewer123")
    print("  Role: Read-only")
    print("\n" + "="*60 + "\n")

def main():
    """Main setup function"""
    print("\n🔐 AutoGluon Churn Prediction - Security Setup")
    print("=" * 60 + "\n")
    
    # Create log directories
    print("Step 1: Creating log directories...")
    create_log_directories()
    print()
    
    # Create .env file
    print("Step 2: Setting up environment variables...")
    create_env_file()
    print()
    
    # Check dependencies
    print("Step 3: Checking dependencies...")
    deps_ok = check_dependencies()
    print()
    
    # Display credentials
    display_default_credentials()
    
    # Next steps
    print("NEXT STEPS:")
    print("=" * 60)
    
    if not deps_ok:
        print("1. Install dependencies: pip install -r requirements.txt")
    else:
        print("1. ✅ Dependencies installed")
    
    print("2. Review and customize config/security.yaml")
    print("3. Start the API: uvicorn app:app --reload")
    print("4. Start the dashboard: streamlit run dashboard.py")
    print("5. Read SECURITY.md for detailed documentation")
    print()
    print("🔒 Security Tips:")
    print("   - Never commit .env to version control")
    print("   - Change default passwords in production")
    print("   - Enable HTTPS for production deployment")
    print("   - Review audit logs regularly")
    print()
    print("✅ Setup complete! You're ready to go.\n")

if __name__ == "__main__":
    main()
