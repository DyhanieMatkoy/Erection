#!/usr/bin/env python3
"""
Analyze migration dependencies to find cycles and issues
"""
import os
import re
from pathlib import Path

def analyze_migrations():
    """Analyze all migration files and their dependencies"""
    migrations_dir = Path('alembic/versions')
    migrations = []

    for file in migrations_dir.glob('*.py'):
        if file.name.startswith('__'):
            continue
        
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract revision and down_revision
            revision_match = re.search(r'revision.*?[\'\"](.*?)[\'\"]', content)
            down_revision_match = re.search(r'down_revision.*?[\'\"](.*?)[\'\"]', content)
            
            revision = revision_match.group(1) if revision_match else 'None'
            down_revision = down_revision_match.group(1) if down_revision_match else 'None'
            
            migrations.append({
                'file': file.name,
                'revision': revision,
                'down_revision': down_revision
            })
        except Exception as e:
            print(f"Error reading {file.name}: {e}")

    # Sort by filename for better readability
    migrations.sort(key=lambda x: x['file'])

    print('Migration Dependencies:')
    print('=' * 100)
    print(f"{'File':<50} | {'Revision':<30} | {'Down Revision':<30}")
    print('=' * 100)
    
    for m in migrations:
        print(f"{m['file']:<50} | {m['revision']:<30} | {m['down_revision']:<30}")
    
    return migrations

def find_cycles(migrations):
    """Find cycles in migration dependencies"""
    print('\n🔍 Looking for cycles...')
    
    # Build dependency graph
    graph = {}
    for m in migrations:
        graph[m['revision']] = m['down_revision']
    
    # Check for cycles
    visited = set()
    rec_stack = set()
    
    def has_cycle(node):
        if node in rec_stack:
            return True
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        
        if node in graph and graph[node] != 'None':
            if has_cycle(graph[node]):
                return True
        
        rec_stack.remove(node)
        return False
    
    cycles_found = []
    for revision in graph:
        if revision not in visited:
            if has_cycle(revision):
                cycles_found.append(revision)
    
    if cycles_found:
        print(f"❌ Cycles found involving: {cycles_found}")
    else:
        print("✅ No cycles detected")
    
    return cycles_found

def find_missing_dependencies(migrations):
    """Find missing dependencies"""
    print('\n🔍 Looking for missing dependencies...')
    
    all_revisions = {m['revision'] for m in migrations}
    missing = []
    
    for m in migrations:
        if m['down_revision'] != 'None' and m['down_revision'] not in all_revisions:
            missing.append({
                'file': m['file'],
                'revision': m['revision'],
                'missing_dep': m['down_revision']
            })
    
    if missing:
        print("❌ Missing dependencies found:")
        for m in missing:
            print(f"  {m['file']} -> missing: {m['missing_dep']}")
    else:
        print("✅ All dependencies found")
    
    return missing

if __name__ == "__main__":
    migrations = analyze_migrations()
    cycles = find_cycles(migrations)
    missing = find_missing_dependencies(migrations)
    
    print(f"\n📊 Summary:")
    print(f"  Total migrations: {len(migrations)}")
    print(f"  Cycles found: {len(cycles)}")
    print(f"  Missing dependencies: {len(missing)}")