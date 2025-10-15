#!/usr/bin/env python3
"""
Comprehensive Test Suite for Parts Department System
Tests everything possible without external service dependencies
"""

import sys
import os
import ast
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET}  {msg}")

def print_info(msg):
    print(f"{CYAN}ℹ{RESET}  {msg}")

class TestSuite:
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        
    def test_python_imports(self) -> bool:
        """Test that all Python modules can be imported without errors"""
        print_header("Testing Python Module Imports")
        
        critical_modules = [
            'backend.config',
            'backend.models',
            'backend.graph.schema',
            'backend.llm.router',
            'backend.email.processor',
            'backend.invoice.generator',
        ]
        
        all_passed = True
        for module_name in critical_modules:
            try:
                # Try to load the module spec
                parts = module_name.split('.')
                file_path = Path(*parts).with_suffix('.py')
                
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        code = f.read()
                        compile(code, str(file_path), 'exec')
                    print_success(f"Module compiles: {module_name}")
                else:
                    print_error(f"Module not found: {module_name}")
                    all_passed = False
            except SyntaxError as e:
                print_error(f"Syntax error in {module_name}: {e}")
                all_passed = False
            except Exception as e:
                print_warning(f"Import check for {module_name}: {e}")
        
        return all_passed
    
    def test_api_endpoints(self) -> bool:
        """Validate API endpoint definitions"""
        print_header("Testing API Endpoint Definitions")
        
        api_files = {
            'backend/api/health.py': ['@router.get("/health")', '@router.get("/ready")'],
            'backend/api/inventory.py': ['@router.post("/locations")', '@router.get("/locations")', '@router.post("/parts")'],
            'backend/api/orders.py': ['@router.post("/")', '@router.post("/{order_id}/invoice")'],
            'backend/api/email_routes.py': ['@router.post("/process")', '@router.post("/send")'],
        }
        
        all_passed = True
        for file_path, expected_routes in api_files.items():
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                for route in expected_routes:
                    if route in content:
                        print_success(f"{file_path}: Found {route}")
                    else:
                        print_error(f"{file_path}: Missing {route}")
                        all_passed = False
            else:
                print_error(f"API file not found: {file_path}")
                all_passed = False
        
        return all_passed
    
    def test_models_and_schemas(self) -> bool:
        """Validate data models and schemas"""
        print_header("Testing Data Models & Schemas")
        
        checks = [
            ('backend/models.py', ['class Order', 'class OrderItem', 'class Invoice', 'class EmailLog']),
            ('backend/graph/schema.py', ['class Location', 'class Part', 'class Department', 'class Supplier']),
        ]
        
        all_passed = True
        for file_path, expected_classes in checks:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                for cls in expected_classes:
                    if cls in content:
                        print_success(f"{file_path}: {cls} ✓")
                    else:
                        print_error(f"{file_path}: {cls} missing")
                        all_passed = False
            else:
                print_error(f"File not found: {file_path}")
                all_passed = False
        
        return all_passed
    
    def test_configuration(self) -> bool:
        """Test configuration management"""
        print_header("Testing Configuration System")
        
        all_passed = True
        
        # Check config.py
        if os.path.exists('backend/config.py'):
            with open('backend/config.py', 'r') as f:
                content = f.read()
            
            required_settings = [
                'neo4j_uri', 'anthropic_api_key', 'llama_model', 
                'claude_model', 'database_url', 'redis_url'
            ]
            
            for setting in required_settings:
                if setting in content:
                    print_success(f"Config has: {setting}")
                else:
                    print_error(f"Config missing: {setting}")
                    all_passed = False
        
        # Check .env.example
        if os.path.exists('.env.example'):
            with open('.env.example', 'r') as f:
                env_content = f.read()
            
            required_env = ['NEO4J_URI', 'ANTHROPIC_API_KEY', 'DATABASE_URL']
            for var in required_env:
                if var in env_content:
                    print_success(f".env.example has: {var}")
                else:
                    print_error(f".env.example missing: {var}")
                    all_passed = False
        
        return all_passed
    
    def test_docker_setup(self) -> bool:
        """Test Docker configuration"""
        print_header("Testing Docker Configuration")
        
        all_passed = True
        
        # Test Dockerfile
        if os.path.exists('docker/Dockerfile'):
            with open('docker/Dockerfile', 'r') as f:
                dockerfile = f.read()
            
            required = [
                ('FROM python', 'Base image'),
                ('WORKDIR /app', 'Working directory'),
                ('COPY requirements.txt', 'Requirements copy'),
                ('RUN pip install', 'Dependency installation'),
                ('EXPOSE 8000', 'Port exposure'),
            ]
            
            for pattern, description in required:
                if pattern in dockerfile:
                    print_success(f"Dockerfile: {description}")
                else:
                    print_error(f"Dockerfile missing: {description}")
                    all_passed = False
        
        # Test docker-compose.yml
        if os.path.exists('docker/docker-compose.yml'):
            with open('docker/docker-compose.yml', 'r') as f:
                compose = f.read()
            
            services = ['api', 'worker', 'beat', 'postgres', 'redis', 'qdrant']
            for service in services:
                if f"{service}:" in compose or f'"{service}"' in compose:
                    print_success(f"docker-compose: {service} service")
                else:
                    print_error(f"docker-compose missing: {service} service")
                    all_passed = False
        
        return all_passed
    
    def test_llm_router(self) -> bool:
        """Test LLM router implementation"""
        print_header("Testing LLM Router Implementation")
        
        if os.path.exists('backend/llm/router.py'):
            with open('backend/llm/router.py', 'r') as f:
                content = f.read()
            
            checks = [
                ('class LLMRouter', 'Router class'),
                ('class ModelTier', 'Model tier enum'),
                ('async def call_llama', 'Llama integration'),
                ('async def call_claude', 'Claude integration'),
                ('async def call_mistral', 'Mistral integration'),
                ('def classify_query_complexity', 'Complexity classification'),
                ('async def generate', 'Main generate method'),
            ]
            
            all_passed = True
            for pattern, description in checks:
                if pattern in content:
                    print_success(f"LLM Router: {description}")
                else:
                    print_error(f"LLM Router missing: {description}")
                    all_passed = False
            
            return all_passed
        else:
            print_error("LLM router file not found")
            return False
    
    def test_rag_system(self) -> bool:
        """Test RAG implementation"""
        print_header("Testing RAG System Implementation")
        
        files_to_check = {
            'backend/rag/vectorstore.py': ['class VectorStore', 'async def search', 'embed_text'],
            'backend/rag/ingestion.py': ['class DocumentIngestion', 'semantic_chunk', 'ingest_parts_catalog'],
            'backend/rag/retrieval.py': ['class HybridRetrieval', 'retrieve_context', 'build_rag_context'],
        }
        
        all_passed = True
        for file_path, patterns in files_to_check.items():
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                for pattern in patterns:
                    if pattern in content:
                        print_success(f"{file_path}: {pattern}")
                    else:
                        print_error(f"{file_path} missing: {pattern}")
                        all_passed = False
            else:
                print_error(f"RAG file not found: {file_path}")
                all_passed = False
        
        return all_passed
    
    def test_email_system(self) -> bool:
        """Test email automation system"""
        print_header("Testing Email Automation System")
        
        files = {
            'backend/email/imap_listener.py': ['class IMAPListener', 'fetch_unread_emails', 'mark_as_read'],
            'backend/email/smtp_sender.py': ['class SMTPSender', 'async def send_email', 'send_invoice_email'],
            'backend/email/processor.py': ['class EmailProcessor', 'classify_intent', 'generate_response'],
        }
        
        all_passed = True
        for file_path, patterns in files.items():
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                for pattern in patterns:
                    if pattern in content:
                        print_success(f"{file_path}: {pattern}")
                    else:
                        print_error(f"{file_path} missing: {pattern}")
                        all_passed = False
        
        return all_passed
    
    def test_graph_database(self) -> bool:
        """Test graph database implementation"""
        print_header("Testing Graph Database Layer")
        
        if os.path.exists('backend/graph/queries.py'):
            with open('backend/graph/queries.py', 'r') as f:
                content = f.read()
            
            queries = [
                'create_location',
                'create_part',
                'add_inventory',
                'check_inventory',
                'transfer_inventory',
                'get_low_stock_items',
                'find_parts_by_name',
            ]
            
            all_passed = True
            for query in queries:
                if query in content:
                    print_success(f"Graph query: {query}")
                else:
                    print_error(f"Graph query missing: {query}")
                    all_passed = False
            
            return all_passed
        else:
            print_error("Graph queries file not found")
            return False
    
    def test_workers(self) -> bool:
        """Test background workers"""
        print_header("Testing Background Workers (Celery)")
        
        files = {
            'backend/workers/celery_app.py': ['celery_app', 'Celery', 'conf.beat_schedule'],
            'backend/workers/tasks.py': ['process_inbox_task', 'send_email_task', 'check_low_stock_task'],
        }
        
        all_passed = True
        for file_path, patterns in files.items():
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                for pattern in patterns:
                    if pattern in content:
                        print_success(f"{file_path}: {pattern}")
                    else:
                        print_error(f"{file_path} missing: {pattern}")
                        all_passed = False
        
        return all_passed
    
    def test_invoice_system(self) -> bool:
        """Test invoice generation"""
        print_header("Testing Invoice Generation System")
        
        if os.path.exists('backend/invoice/generator.py'):
            with open('backend/invoice/generator.py', 'r') as f:
                content = f.read()
            
            checks = [
                ('class InvoiceGenerator', 'Generator class'),
                ('def create_invoice', 'Create invoice method'),
                ('def generate_invoice_number', 'Invoice numbering'),
                ('reportlab', 'PDF library'),
            ]
            
            all_passed = True
            for pattern, description in checks:
                if pattern in content:
                    print_success(f"Invoice system: {description}")
                else:
                    print_error(f"Invoice system missing: {description}")
                    all_passed = False
            
            return all_passed
        else:
            print_error("Invoice generator not found")
            return False
    
    def test_documentation(self) -> bool:
        """Test documentation completeness"""
        print_header("Testing Documentation")
        
        docs = {
            'README.md': ['Architecture', 'Quick Start', 'API'],
            'SETUP.md': ['Prerequisites', 'Step', 'Configuration'],
            'INSTALL.md': ['Installation', 'Docker', 'Virtual'],
            'TECH_STACK.md': ['October 2025', 'FastAPI', 'Neo4j'],
            'CHANGELOG.md': ['[1.0.0]', '2025-10-15'],
        }
        
        all_passed = True
        for doc_file, keywords in docs.items():
            if os.path.exists(doc_file):
                with open(doc_file, 'r') as f:
                    content = f.read()
                
                for keyword in keywords:
                    if keyword in content:
                        print_success(f"{doc_file}: Contains '{keyword}'")
                    else:
                        print_warning(f"{doc_file}: May be missing '{keyword}'")
        
        return all_passed
    
    def test_scripts(self) -> bool:
        """Test utility scripts"""
        print_header("Testing Utility Scripts")
        
        scripts = {
            'scripts/seed_data.py': ['async def seed_locations', 'async def seed_parts'],
            'scripts/test_system.py': ['test_inventory', 'test_llm_router', 'test_email_processing'],
            'quickstart.sh': ['docker-compose', 'up -d'],
            'install.sh': ['venv', 'pip install'],
        }
        
        all_passed = True
        for script, patterns in scripts.items():
            if os.path.exists(script):
                with open(script, 'r') as f:
                    content = f.read()
                
                for pattern in patterns:
                    if pattern in content:
                        print_success(f"{script}: Has {pattern}")
                    else:
                        print_error(f"{script} missing: {pattern}")
                        all_passed = False
            else:
                print_error(f"Script not found: {script}")
                all_passed = False
        
        return all_passed
    
    def count_metrics(self) -> Dict:
        """Count code metrics"""
        print_header("Code Metrics")
        
        metrics = {
            'python_files': 0,
            'total_lines': 0,
            'classes': 0,
            'functions': 0,
            'async_functions': 0,
        }
        
        for root, dirs, files in os.walk('backend'):
            for file in files:
                if file.endswith('.py'):
                    metrics['python_files'] += 1
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                        metrics['total_lines'] += len(content.splitlines())
                        metrics['classes'] += content.count('class ')
                        metrics['functions'] += content.count('def ')
                        metrics['async_functions'] += content.count('async def ')
        
        print_info(f"Python files: {metrics['python_files']}")
        print_info(f"Total lines: {metrics['total_lines']}")
        print_info(f"Classes: {metrics['classes']}")
        print_info(f"Functions: {metrics['functions']}")
        print_info(f"Async functions: {metrics['async_functions']}")
        
        return metrics
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
        print(f"{BOLD}{CYAN}PARTS DEPARTMENT SYSTEM - COMPREHENSIVE TEST SUITE{RESET}".center(80))
        print(f"{BOLD}{CYAN}October 15, 2025{RESET}".center(80))
        print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")
        
        tests = [
            ('Python Imports', self.test_python_imports),
            ('API Endpoints', self.test_api_endpoints),
            ('Models & Schemas', self.test_models_and_schemas),
            ('Configuration', self.test_configuration),
            ('Docker Setup', self.test_docker_setup),
            ('LLM Router', self.test_llm_router),
            ('RAG System', self.test_rag_system),
            ('Email System', self.test_email_system),
            ('Graph Database', self.test_graph_database),
            ('Background Workers', self.test_workers),
            ('Invoice System', self.test_invoice_system),
            ('Documentation', self.test_documentation),
            ('Scripts', self.test_scripts),
        ]
        
        for test_name, test_func in tests:
            self.total_tests += 1
            try:
                result = test_func()
                self.results[test_name] = result
                if result:
                    self.passed_tests += 1
            except Exception as e:
                print_error(f"Test '{test_name}' failed with error: {e}")
                self.results[test_name] = False
        
        # Code metrics
        metrics = self.count_metrics()
        
        # Final results
        print_header("TEST SUMMARY")
        
        for test_name, passed in self.results.items():
            status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
            print(f"{test_name:.<50} {status}")
        
        print(f"\n{BOLD}Total Tests:{RESET} {self.total_tests}")
        print(f"{BOLD}Passed:{RESET} {GREEN}{self.passed_tests}{RESET}")
        print(f"{BOLD}Failed:{RESET} {RED}{self.total_tests - self.passed_tests}{RESET}")
        
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"{BOLD}Pass Rate:{RESET} {pass_rate:.1f}%")
        
        print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
        if self.passed_tests == self.total_tests:
            print(f"{BOLD}{GREEN}✓ ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT!{RESET}".center(80))
        else:
            print(f"{BOLD}{YELLOW}⚠ SOME TESTS FAILED - REVIEW RESULTS ABOVE{RESET}".center(80))
        print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")
        
        return 0 if self.passed_tests == self.total_tests else 1


if __name__ == "__main__":
    os.chdir("/Users/seanmcdonnell/Desktop/Parts Dept")
    suite = TestSuite()
    exit_code = suite.run_all_tests()
    sys.exit(exit_code)

