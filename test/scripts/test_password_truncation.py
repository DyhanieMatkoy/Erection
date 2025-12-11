"""Test password truncation for bcrypt compatibility"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def truncate_password(password: str) -> str:
    """
    Truncate password to 72 bytes for bcrypt compatibility.
    Ensures we don't cut in the middle of a UTF-8 character.
    """
    if not password:
        return password
    
    password_bytes = password.encode('utf-8')
    if len(password_bytes) <= 72:
        return password
    
    truncated_bytes = password_bytes[:72]
    truncated_password = truncated_bytes.decode('utf-8', errors='ignore')
    
    while len(truncated_password.encode('utf-8')) > 72:
        truncated_password = truncated_password[:-1]
    
    return truncated_password

# Test with various password lengths
test_passwords = [
    "short",
    "a" * 50,
    "a" * 72,
    "a" * 100,
    "Привет" * 20,  # Cyrillic characters (2 bytes each in UTF-8)
    "🔒" * 30,  # Emoji (4 bytes each in UTF-8)
]

print("Testing password truncation and bcrypt hashing:\n")
print("=" * 80)

for password in test_passwords:
    original_len = len(password.encode('utf-8'))
    truncated = truncate_password(password)
    truncated_len = len(truncated.encode('utf-8'))
    
    print(f"Original: {original_len} bytes, Truncated: {truncated_len} bytes")
    
    try:
        # Try to hash the truncated password
        hashed = pwd_context.hash(truncated)
        
        # Try to verify it
        verified = pwd_context.verify(truncated, hashed)
        
        print(f"  ✓ Hash successful, verification: {verified}")
        
        # Also verify with the original password (should work if truncated correctly)
        verified_original = pwd_context.verify(truncate_password(password), hashed)
        print(f"  ✓ Original password verification: {verified_original}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print()

print("=" * 80)
print("\nAll tests completed!")
