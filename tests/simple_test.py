import unittest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class SimpleTest(unittest.TestCase):
    def test_addition(self):
        """Simple test to verify the test framework is working"""
        print("\nRunning simple test...")
        self.assertEqual(1 + 1, 2)
        print("✓ Simple test passed")

if __name__ == '__main__':
    print("Starting simple test...")
    unittest.main()
