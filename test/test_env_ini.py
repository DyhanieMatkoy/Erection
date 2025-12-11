#!/usr/bin/env python3
"""Test script to debug env.ini reading"""
import os
import configparser

print("=" * 60)
print("ENV.INI DEBUG TEST")
print("=" * 60)

# Check current directory
print(f"\nCurrent working directory: {os.getcwd()}")

# Check if env.ini exists
env_file = os.path.join(os.getcwd(), 'env.ini')
print(f"Looking for env.ini at: {env_file}")
print(f"File exists: {os.path.exists(env_file)}")

if os.path.exists(env_file):
    print("\n--- File Contents (raw) ---")
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(repr(content))
        print(content)
    
    print("\n--- ConfigParser Method ---")
    config = configparser.ConfigParser()
    config.read(env_file, encoding='utf-8')
    
    print(f"Sections: {config.sections()}")
    print(f"Has DEFAULT: {'DEFAULT' in config}")
    
    if 'DEFAULT' in config:
        print(f"DEFAULT items: {list(config['DEFAULT'].items())}")
        if config.has_option('DEFAULT', 'login'):
            print(f"Login from DEFAULT: {config.get('DEFAULT', 'login')}")
        if config.has_option('DEFAULT', 'password'):
            print(f"Password from DEFAULT: {config.get('DEFAULT', 'password')}")
    
    print("\n--- Simple Key=Value Method ---")
    username = None
    password = None
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            print(f"Processing line: {repr(line)}")
            if line.startswith('login='):
                username = line.split('=', 1)[1]
                print(f"  -> Found username: {username}")
            elif line.startswith('password='):
                password = line.split('=', 1)[1]
                print(f"  -> Found password: {password}")
    
    print(f"\nFinal result: username={username}, password={password}")
else:
    print("\nenv.ini file not found!")

print("\n" + "=" * 60)
