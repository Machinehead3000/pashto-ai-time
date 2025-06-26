#!/usr/bin/env python3
"""
Test runner script for the Pashto AI project.
Supports both unit tests and performance testing.
"""
import sys
import os
import time
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# File handler - always use UTF-8
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# Console handler with UTF-8 support
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
# Set console encoding to UTF-8
import io
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
root_logger.addHandler(console_handler)
logger = logging.getLogger(__name__)

def run_unit_tests(test_path: str = "tests/", coverage: bool = True) -> int:
    """Run unit tests with optional coverage reporting."""
    logger.info("🚀 Starting unit test suite...")
    
    cmd = [sys.executable, "-m", "pytest"]
    
    if coverage:
        cmd.extend([
            "--cov=aichat",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-fail-under=80"
        ])
    
    cmd.extend(["-v", test_path])
    
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def run_performance_tests() -> int:
    """Run performance tests and generate reports."""
    logger.info("🚀 Starting performance tests...")
    
    # Import here to avoid circular imports
    from tests.performance import test_performance
    
    # Run performance tests
    test_suite = unittest.TestLoader().loadTestsFromModule(test_performance)
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return 0 if result.wasSuccessful() else 1

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Run tests for Pashto AI")
    parser.add_argument(
        "--unit", action="store_true", 
        help="Run unit tests (default)"
    )
    parser.add_argument(
        "--performance", action="store_true", 
        help="Run performance tests"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all tests (unit + performance)"
    )
    parser.add_argument(
        "test_path", nargs="?", default="tests/",
        help="Test directory or file to run"
    )
    
    args = parser.parse_args()
    
    # Default to running unit tests if no specific test type is specified
    if not any([args.unit, args.performance, args.all]):
        args.unit = True
    
    # Run the selected tests
    results = {}
    
    if args.unit or args.all:
        results["unit"] = run_unit_tests(args.test_path)
    
    if args.performance or args.all:
        results["performance"] = run_performance_tests()
    
    # Report results
    logger.info("\n" + "=" * 80)
    logger.info("TEST RESULTS")
    logger.info("=" * 80)
    
    for test_type, result in results.items():
        status = "PASSED" if result == 0 else "FAILED"
        logger.info(f"{test_type.upper():<15} {status}")
    
    logger.info("=" * 80)
    
    # Return non-zero if any tests failed
    sys.exit(1 if any(r != 0 for r in results.values()) else 0)

if __name__ == "__main__":
    # Add project root to path
    project_root = str(Path(__file__).parent.absolute())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    import unittest  # Import here to avoid circular imports
    
    logger.info(f"Running tests. Logging to {log_file}")
    main()
