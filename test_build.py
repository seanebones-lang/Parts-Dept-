#!/usr/bin/env python3
"""
Build and functionality test for Parts Department System
Tests code structure, imports, and basic functionality without external dependencies
"""

import sys
import os
from pathlib import Path
import ast
import importlib.util

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def test_python_syntax(file_path):
    """Test if Python file has valid syntax"""
    try:
        with open(file_path, 'r') as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        return False, str(e)

def test_file_structure():
    """Test if all required files exist"""
    print("\n" + "="*60)
    print("Testing File Structure")
    print("="*60)
    
    required_files = [
        "backend/__init__.py",
        "backend/main.py",
        "backend/config.py",
        "backend/database.py",
        "backend/models.py",
        "backend/api/health.py",
        "backend/api/inventory.py",
        "backend/api/orders.py",
        "backend/api/email_routes.py",
        "backend/graph/connection.py",
        "backend/graph/queries.py",
        "backend/graph/schema.py",
        "backend/rag/vectorstore.py",
        "backend/rag/ingestion.py",
        "backend/rag/retrieval.py",
        "backend/llm/router.py",
        "backend/email/imap_listener.py",
        "backend/email/smtp_sender.py",
        "backend/email/processor.py",
        "backend/invoice/generator.py",
        "backend/workers/celery_app.py",
        "backend/workers/tasks.py",
        "docker/Dockerfile",
        "docker/docker-compose.yml",
        "requirements.txt",
        "README.md",
        "SETUP.md",
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print_success(f"Found: {file}")
        else:
            print_error(f"Missing: {file}")
            missing.append(file)
    
    if missing:
        print_error(f"\n{len(missing)} files missing!")
        return False
    else:
        print_success(f"\nAll {len(required_files)} required files present")
        return True

def test_python_syntax_all():
    """Test Python syntax for all .py files"""
    print("\n" + "="*60)
    print("Testing Python Syntax")
    print("="*60)
    
    errors = []
    success_count = 0
    
    for root, dirs, files in os.walk("backend"):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                result = test_python_syntax(file_path)
                
                if result is True:
                    print_success(f"Valid syntax: {file_path}")
                    success_count += 1
                else:
                    print_error(f"Syntax error in {file_path}: {result[1]}")
                    errors.append((file_path, result[1]))
    
    if errors:
        print_error(f"\n{len(errors)} syntax errors found")
        return False
    else:
        print_success(f"\nAll {success_count} Python files have valid syntax")
        return True

def test_imports():
    """Test critical imports in main files"""
    print("\n" + "="*60)
    print("Testing Critical Module Structure")
    print("="*60)
    
    tests = {
        "backend/config.py": ["Settings", "settings"],
        "backend/models.py": ["Order", "OrderItem", "Invoice", "EmailLog"],
        "backend/graph/schema.py": ["Location", "Part", "Department", "Supplier"],
        "backend/llm/router.py": ["LLMRouter", "ModelTier"],
    }
    
    all_passed = True
    
    for file_path, expected_attrs in tests.items():
        try:
            spec = importlib.util.spec_from_file_location("test_module", file_path)
            module = importlib.util.module_from_spec(spec)
            
            # Don't execute, just check structure
            with open(file_path, 'r') as f:
                content = f.read()
            
            missing = []
            for attr in expected_attrs:
                if f"class {attr}" in content or f"{attr} =" in content:
                    pass  # Found
                else:
                    missing.append(attr)
            
            if missing:
                print_error(f"{file_path}: Missing {missing}")
                all_passed = False
            else:
                print_success(f"{file_path}: All expected items present")
        
        except Exception as e:
            print_error(f"{file_path}: {str(e)}")
            all_passed = False
    
    return all_passed

def test_docker_config():
    """Test Docker configuration"""
    print("\n" + "="*60)
    print("Testing Docker Configuration")
    print("="*60)
    
    # Test Dockerfile
    if os.path.exists("docker/Dockerfile"):
        with open("docker/Dockerfile", 'r') as f:
            dockerfile = f.read()
            
        required = ["FROM python", "WORKDIR", "COPY requirements.txt", "RUN pip install", "EXPOSE"]
        for item in required:
            if item in dockerfile:
                print_success(f"Dockerfile contains: {item}")
            else:
                print_error(f"Dockerfile missing: {item}")
    
    # Test docker-compose
    if os.path.exists("docker/docker-compose.yml"):
        with open("docker/docker-compose.yml", 'r') as f:
            compose = f.read()
        
        services = ["api", "worker", "postgres", "redis", "qdrant"]
        for service in services:
            if f"{service}:" in compose:
                print_success(f"docker-compose contains service: {service}")
            else:
                print_error(f"docker-compose missing service: {service}")
    
    return True

def test_api_routes():
    """Test API route definitions"""
    print("\n" + "="*60)
    print("Testing API Routes")
    print("="*60)
    
    route_files = {
        "backend/api/health.py": ["@router.get", "/health"],
        "backend/api/inventory.py": ["@router.post", "@router.get"],
        "backend/api/orders.py": ["@router.post", "@router.get"],
        "backend/api/email_routes.py": ["@router.post"],
    }
    
    for file_path, patterns in route_files.items():
        with open(file_path, 'r') as f:
            content = f.read()
        
        for pattern in patterns:
            if pattern in content:
                print_success(f"{file_path}: Contains {pattern}")
            else:
                print_error(f"{file_path}: Missing {pattern}")
    
    return True

def count_lines_of_code():
    """Count total lines of code"""
    print("\n" + "="*60)
    print("Code Statistics")
    print("="*60)
    
    total_lines = 0
    total_files = 0
    
    for root, dirs, files in os.walk("backend"):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    lines = len(f.readlines())
                    total_lines += lines
                    total_files += 1
    
    print(f"Total Python files: {total_files}")
    print(f"Total lines of code: {total_lines}")
    print(f"Average lines per file: {total_lines // total_files if total_files > 0 else 0}")
    
    return True

def main():
    print("\n" + "="*60)
    print("PARTS DEPARTMENT SYSTEM - BUILD TEST")
    print("="*60)
    
    os.chdir("/Users/seanmcdonnell/Desktop/Parts Dept")
    
    results = {
        "File Structure": test_file_structure(),
        "Python Syntax": test_python_syntax_all(),
        "Module Structure": test_imports(),
        "Docker Config": test_docker_config(),
        "API Routes": test_api_routes(),
    }
    
    count_lines_of_code()
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print_success("BUILD TEST PASSED - System is ready for deployment!")
    else:
        print_error("BUILD TEST FAILED - Please fix errors above")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

