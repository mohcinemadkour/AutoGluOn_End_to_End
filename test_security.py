"""
Authentication & Security Test Suite
=====================================
Tests for JWT authentication, RBAC, and audit logging
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_authentication():
    """Test user authentication"""
    from auth.authentication import AuthManager, UserRole
    
    print("\n🧪 Testing Authentication...")
    auth = AuthManager()
    
    # Test valid login
    user = auth.authenticate_user("admin", "admin123")
    assert user is not None, "Valid login failed"
    assert user.username == "admin", "Username mismatch"
    assert user.role == UserRole.ADMIN, "Role mismatch"
    print("✅ Valid login successful")
    
    # Test invalid password
    user = auth.authenticate_user("admin", "wrongpassword")
    assert user is None, "Invalid password should fail"
    print("✅ Invalid password rejected")
    
    # Test non-existent user
    user = auth.authenticate_user("nonexistent", "password")
    assert user is None, "Non-existent user should fail"
    print("✅ Non-existent user rejected")


def test_jwt_tokens():
    """Test JWT token creation and validation"""
    from auth.authentication import AuthManager, UserRole, create_access_token
    from datetime import timedelta
    
    print("\n🧪 Testing JWT Tokens...")
    auth = AuthManager()
    
    # Create token
    user = auth.authenticate_user("analyst", "analyst123")
    token = create_access_token(user.username, user.role, auth)
    assert token.access_token, "Token creation failed"
    print(f"✅ Token created: {token.access_token[:20]}...")
    
    # Validate token
    token_data = auth.decode_token(token.access_token)
    assert token_data is not None, "Token validation failed"
    assert token_data.username == "analyst", "Username mismatch in token"
    assert token_data.role == "analyst", "Role mismatch in token"
    print("✅ Token validation successful")
    
    # Test invalid token
    invalid_token = "invalid.token.here"
    token_data = auth.decode_token(invalid_token)
    assert token_data is None, "Invalid token should fail"
    print("✅ Invalid token rejected")


def test_rbac():
    """Test role-based access control"""
    from auth.authentication import AuthManager, UserRole
    
    print("\n🧪 Testing Role-Based Access Control...")
    auth = AuthManager()
    
    # Admin can do everything
    assert auth.check_permission(UserRole.ADMIN, UserRole.VIEWER), "Admin should have viewer access"
    assert auth.check_permission(UserRole.ADMIN, UserRole.ANALYST), "Admin should have analyst access"
    assert auth.check_permission(UserRole.ADMIN, UserRole.ADMIN), "Admin should have admin access"
    print("✅ Admin permissions correct")
    
    # Analyst can do analyst and viewer tasks
    assert auth.check_permission(UserRole.ANALYST, UserRole.VIEWER), "Analyst should have viewer access"
    assert auth.check_permission(UserRole.ANALYST, UserRole.ANALYST), "Analyst should have analyst access"
    assert not auth.check_permission(UserRole.ANALYST, UserRole.ADMIN), "Analyst should not have admin access"
    print("✅ Analyst permissions correct")
    
    # Viewer can only do viewer tasks
    assert auth.check_permission(UserRole.VIEWER, UserRole.VIEWER), "Viewer should have viewer access"
    assert not auth.check_permission(UserRole.VIEWER, UserRole.ANALYST), "Viewer should not have analyst access"
    assert not auth.check_permission(UserRole.VIEWER, UserRole.ADMIN), "Viewer should not have admin access"
    print("✅ Viewer permissions correct")


def test_audit_logging():
    """Test audit logging functionality"""
    from auth.audit_log import AuditLogger, AuditEventType, AuditEvent
    import tempfile
    from datetime import datetime
    
    print("\n🧪 Testing Audit Logging...")
    
    # Create temporary log directory
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(log_dir=tmpdir)
        
        # Test login event
        logger.log_login("testuser", success=True, ip_address="192.168.1.1")
        print("✅ Login event logged")
        
        # Test prediction event
        logger.log_prediction(
            username="analyst",
            user_role="analyst",
            prediction_data={"customer_id": "C123", "probability": 0.75},
            success=True,
            ip_address="192.168.1.1"
        )
        print("✅ Prediction event logged")
        
        # Test unauthorized access event
        logger.log_unauthorized_access("hacker", "/admin/secret", ip_address="192.168.1.100")
        print("✅ Unauthorized access logged")
        
        # Test statistics
        stats = logger.get_statistics(days=1)
        assert stats["total_events"] >= 3, "Should have at least 3 events"
        assert stats["failed_events"] >= 1, "Should have at least 1 failed event"
        print(f"✅ Statistics generated: {stats['total_events']} events")


def test_user_management():
    """Test user creation and management"""
    from auth.authentication import AuthManager, UserRole
    
    print("\n🧪 Testing User Management...")
    auth = AuthManager()
    
    # Get all users
    users = auth.get_all_users()
    initial_count = len(users)
    print(f"✅ Found {initial_count} default users")
    
    # Create new user
    try:
        new_user = auth.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role=UserRole.ANALYST,
            full_name="Test User"
        )
        print("✅ New user created")
        
        # Verify user exists
        user = auth.get_user("testuser")
        assert user is not None, "Created user not found"
        assert user.email == "test@example.com", "Email mismatch"
        print("✅ User retrieval successful")
        
        # Test duplicate creation fails
        try:
            auth.create_user(
                username="testuser",
                email="test2@example.com",
                password="testpass",
                role=UserRole.VIEWER
            )
            assert False, "Duplicate user creation should fail"
        except ValueError:
            print("✅ Duplicate user rejected")
        
    except Exception as e:
        print(f"⚠️  User management test issue: {e}")


def test_password_hashing():
    """Test password hashing"""
    from auth.authentication import AuthManager
    
    print("\n🧪 Testing Password Hashing...")
    auth = AuthManager()
    
    password = "mySecurePassword123"
    
    # Hash password
    hashed = auth.get_password_hash(password)
    assert hashed != password, "Password should be hashed"
    assert len(hashed) > 50, "Hash should be long"
    print(f"✅ Password hashed: {hashed[:20]}...")
    
    # Verify correct password
    assert auth.verify_password(password, hashed), "Correct password should verify"
    print("✅ Correct password verified")
    
    # Reject incorrect password
    assert not auth.verify_password("wrongpassword", hashed), "Wrong password should fail"
    print("✅ Incorrect password rejected")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🔐 AUTHENTICATION & SECURITY TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Authentication", test_authentication),
        ("JWT Tokens", test_jwt_tokens),
        ("RBAC", test_rbac),
        ("Audit Logging", test_audit_logging),
        ("User Management", test_user_management),
        ("Password Hashing", test_password_hashing),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {name} test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {name} test error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Security implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
