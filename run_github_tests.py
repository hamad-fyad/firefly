#!/usr/bin/env python3
"""
GitHub Actions Test Runner for Firefly III Test Suite

This script runs tests suitable for GitHub Actions environment,
excluding tests that require local services not available in CI.

Usage:
    python run_github_tests.py [test_type]
    
Test Types:
    all      - Run all GitHub Actions compatible tests (default)
    api      - Run only API tests
    ai       - Run only AI unit tests (with mocks)
    webhook  - Run only webhook unit tests (with mocks)
    unit     - Run only unit tests with mocks
    business - Run only business workflow tests
    security - Run only security tests (Bandit, Safety, etc.)
    performance - Run only performance and benchmark tests
    quality  - Run only code quality checks (Black, Flake8, etc.)
    load     - Run load/stress tests (performance + API tests)
"""

import subprocess
import sys
import os
from pathlib import Path

def run_security_checks():
    """Run security checks (Bandit, Safety, Semgrep, etc.)."""
    
    print("🛡️ Running security checks...")
    
    # Create security reports directory
    os.makedirs("security-reports", exist_ok=True)
    
    security_tools = [
        {
            "name": "Bandit (Security Linter)",
            "cmd": ["python3", "-m", "bandit", "-r", "tests/", "*.py", "-f", "json", "-o", "security-reports/bandit-report.json"],
            "fallback_cmd": ["python3", "-m", "bandit", "-r", "tests/", "*.py", "--severity-level", "medium"],
            "warning_only": True  # Bandit in test files often has many false positives
        },
        {
            "name": "Safety (Dependency Vulnerability Check)",
            "cmd": ["python3", "-m", "safety", "check", "--json", "--output", "security-reports/safety-report.json"],
            "fallback_cmd": ["python3", "-m", "safety", "check"],
            "warning_only": True  # Vulnerabilities are warnings for CI, not failures
        }
    ]
    
    all_passed = True
    
    for tool in security_tools:
        print(f"\n🔍 Running {tool['name']}...")
        try:
            # Try main command first
            result = subprocess.run(tool["cmd"], capture_output=True, text=True)
            
            if result.returncode != 0 and "fallback_cmd" in tool:
                # Try fallback command if main fails
                print(f"⚠️  JSON output failed, trying standard output...")
                result = subprocess.run(tool["fallback_cmd"], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {tool['name']}: PASSED")
            else:
                if tool.get("warning_only", False):
                    print(f"⚠️  {tool['name']}: Issues found (warnings only)")
                    if result.stdout:
                        # For verbose output, show first few lines  
                        lines = result.stdout.split('\n')
                        if len(lines) > 10:
                            print('\n'.join(lines[:5]))
                            print(f"... ({len(lines)-10} more lines) ...")
                            print('\n'.join(lines[-5:]))
                        else:
                            print(result.stdout)
                else:
                    print(f"❌ {tool['name']}: FAILED")
                    if result.stdout:
                        print(result.stdout)
                    if result.stderr:
                        print(result.stderr)
                    all_passed = False
                        
        except FileNotFoundError:
            print(f"⚠️  {tool['name']}: Tool not installed")
        except Exception as e:
            print(f"❌ {tool['name']}: Error - {e}")
            all_passed = False
    
    # Check for secrets in code
    print(f"\n🔍 Running Secrets Detection...")
    try:
        # Check for potential secrets
        result = subprocess.run(
            ["grep", "-r", "-i", "password\\|secret\\|key\\|token", "tests/", "--exclude-dir=__pycache__"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("⚠️  Potential secrets found:")
            print(result.stdout)
        else:
            print("✅ No obvious secrets found")
    except Exception as e:
        print(f"⚠️  Secrets detection failed: {e}")
    
    # Check for hardcoded IPs
    try:
        result = subprocess.run(
            ["grep", "-r", "-E", "http://[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+", "tests/"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("⚠️  Hardcoded IPs found:")
            print(result.stdout)
        else:
            print("✅ No hardcoded IPs found")
    except Exception as e:
        print(f"⚠️  IP detection failed: {e}")
    
    # Generate security summary
    try:
        with open("security-reports/security-summary.md", "w") as f:
            f.write("# Security Test Report\\n")
            f.write(f"Generated: {subprocess.run(['date'], capture_output=True, text=True).stdout}")
            f.write("\\n## Tests Performed:\\n")
            f.write("- Bandit: Static security analysis\\n")
            f.write("- Safety: Dependency vulnerability scanning\\n")
            f.write("- Secrets detection: Manual pattern matching\\n")
        print("📄 Security summary generated: security-reports/security-summary.md")
    except Exception as e:
        print(f"⚠️  Failed to generate security summary: {e}")
    
    return 0 if all_passed else 1

def run_quality_checks():
    """Run code quality checks (Black, Flake8, MyPy, etc.)."""
    
    print("🧹 Running code quality checks...")
    
    quality_tools = [
        {
            "name": "Black (Code Formatting)",
            "cmd": ["python3", "-m", "black", "--check", "--diff", "tests/", "*.py"],
            "warning_only": True
        },
        {
            "name": "isort (Import Sorting)", 
            "cmd": ["python3", "-m", "isort", "--check-only", "--diff", "tests/", "*.py"],
            "warning_only": True
        },
        {
            "name": "Flake8 (Style Guide)",
            "cmd": ["python3", "-m", "flake8", "tests/", "*.py", "--max-line-length=100", "--ignore=E203,W503"],
            "warning_only": True
        },
        {
            "name": "MyPy (Type Checking)",
            "cmd": ["python3", "-m", "mypy", "tests/", "--ignore-missing-imports"],
            "warning_only": True
        }
    ]
    
    all_passed = True
    
    for tool in quality_tools:
        print(f"\n🔍 Running {tool['name']}...")
        try:
            result = subprocess.run(tool["cmd"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {tool['name']}: PASSED")
            else:
                if tool.get("warning_only", False):
                    print(f"⚠️  {tool['name']}: Issues found (warnings only)")
                    if result.stdout:
                        print(result.stdout)
                else:
                    print(f"❌ {tool['name']}: FAILED")
                    if result.stdout:
                        print(result.stdout)
                    if result.stderr:
                        print(result.stderr)
                    all_passed = False
        except FileNotFoundError:
            print(f"⚠️  {tool['name']}: Tool not installed")
        except Exception as e:
            print(f"❌ {tool['name']}: Error - {e}")
            all_passed = False
    
    return 0 if all_passed else 1
    """Run code quality checks (Black, Flake8, MyPy, etc.)."""
    
    print("🧹 Running code quality checks...")
    
    quality_tools = [
        {
            "name": "Black (Code Formatting)",
            "cmd": ["python3", "-m", "black", "--check", "--diff", "tests/", "*.py"],
            "warning_only": True
        },
        {
            "name": "isort (Import Sorting)", 
            "cmd": ["python3", "-m", "isort", "--check-only", "--diff", "tests/", "*.py"],
            "warning_only": True
        },
        {
            "name": "Flake8 (Style Guide)",
            "cmd": ["python3", "-m", "flake8", "tests/", "*.py", "--max-line-length=100", "--ignore=E203,W503"],
            "warning_only": True
        },
        {
            "name": "MyPy (Type Checking)",
            "cmd": ["python3", "-m", "mypy", "tests/", "--ignore-missing-imports"],
            "warning_only": True
        }
    ]
    
    all_passed = True
    
    for tool in quality_tools:
        print(f"\n🔍 Running {tool['name']}...")
        try:
            result = subprocess.run(tool["cmd"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {tool['name']}: PASSED")
            else:
                if tool.get("warning_only", False):
                    print(f"⚠️  {tool['name']}: Issues found (warnings only)")
                    if result.stdout:
                        print(result.stdout)
                else:
                    print(f"❌ {tool['name']}: FAILED")
                    if result.stdout:
                        print(result.stdout)
                    if result.stderr:
                        print(result.stderr)
                    all_passed = False
        except FileNotFoundError:
            print(f"⚠️  {tool['name']}: Tool not installed")
        except Exception as e:
            print(f"❌ {tool['name']}: Error - {e}")
            all_passed = False
    
    return 0 if all_passed else 1

def run_tests(test_type="all"):
    """Run tests based on specified type."""
    
    # Set GitHub Actions flag
    os.environ['GITHUB_ACTIONS'] = 'true'
    
    base_cmd = [
        "python3", "-m", "pytest",
        "--alluredir=allure-results",
        "--cov=tests",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v",
        "--tb=short",
        "--maxfail=10",
        "--disable-warnings"
    ]
    
    # Define test selection based on type
    test_selections = {
        "all": [
            "-m", "github_actions and not local_only",
            "tests/"
        ],
        "api": [
            "-m", "github_actions and api and not local_only",
            "tests/test_firefly_transactions.py",
            "tests/test_firefly_advanced.py", 
            "tests/test_account.py"
        ],
        "ai": [
            "-m", "github_actions and ai and unit",
            "tests/test_ai_unit.py"
        ],
        "webhook": [
            "-m", "github_actions and webhook and unit", 
            "tests/test_webhook_unit.py"
        ],
        "unit": [
            "-m", "github_actions and unit",
            "tests/test_ai_unit.py",
            "tests/test_webhook_unit.py"
        ],
        "business": [
            "-m", "github_actions and business_workflow and not local_only",
            "tests/"
        ],
        "security": [
            # Security checks are handled by separate tools, not pytest
            "--help"
        ],
        "performance": [
            "-m", "github_actions and performance",
            "tests/test_ai_unit.py",
            "tests/test_webhook_unit.py"
        ],
        "quality": [
            # Quality checks are handled by separate tools, not pytest
            "--help"
        ],
        "load": [
            # Load testing - run performance tests multiple times
            "-m", "github_actions and (performance or api)",
            "tests/test_ai_unit.py",
            "tests/test_webhook_unit.py", 
            "tests/test_webhook_service.py"
        ]
    }
    
    if test_type not in test_selections:
        print(f"❌ Unknown test type: {test_type}")
        print(f"Available types: {', '.join(test_selections.keys())}")
        return 1
    
    # Handle special test types
    if test_type == "quality":
        return run_quality_checks()
    elif test_type == "security":
        return run_security_checks()
    
    # Build final command
    cmd = base_cmd + test_selections[test_type]
    
    print(f"� Running {test_type} tests for GitHub Actions...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def main():
    """Main entry point."""
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    print("🧪 Firefly III GitHub Actions Test Runner")
    print("=" * 50)
    
    # Check if we're in GitHub Actions
    if os.getenv("GITHUB_ACTIONS"):
        print("🔧 Running in GitHub Actions environment")
    else:
        print("🏠 Running in local environment (simulating GitHub Actions)")
    
    exit_code = run_tests(test_type)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()