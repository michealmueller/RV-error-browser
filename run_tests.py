#!/usr/bin/env python3
import sys
import pytest

def main():
    """Run the test suite."""
    # Add command line arguments
    args = sys.argv[1:] or ['tests']
    
    # Run pytest with the provided arguments
    return pytest.main(args)

if __name__ == '__main__':
    sys.exit(main()) 