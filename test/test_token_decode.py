"""
Test token decoding
"""
import jwt
import json

# Token from the test
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjQsInVzZXJuYW1lIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NjM3ODU4NjUsImlhdCI6MTc2Mzc1NzA2NX0.y3NzBE0OqOd12cn2utq90MdVbeFFtZOIKqygCOjxjvU"

# Decode without verification to see payload
try:
    payload = jwt.decode(token, options={"verify_signature": False})
    print("Token payload:")
    print(json.dumps(payload, indent=2))
except Exception as e:
    print(f"Error decoding: {e}")

# Try to decode with verification using the secret from config
from api.config import settings

try:
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    print("\n\nToken verified successfully!")
    print(json.dumps(payload, indent=2))
except jwt.ExpiredSignatureError:
    print("\n\nToken expired!")
except jwt.InvalidTokenError as e:
    print(f"\n\nInvalid token: {e}")
