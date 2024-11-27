"""Module for managing test battles."""
from typing import List, Optional
import json
import os
from battles import Battle

# Cache for tests
_tests: Optional[List[Battle]] = None

def get_tests() -> List[Battle]:
    """Get all available tests."""
    global _tests
    
    if _tests is not None:
        return _tests
        
    if not os.path.exists("data/tests.json"):
        _tests = []
        return []
    
    with open("data/tests.json", "r") as f:
        data = json.load(f)
    
    _tests = [Battle(**test) for test in data["tests"]]
    return _tests

def get_test(test_id: str) -> Optional[Battle]:
    """Get a specific test by ID."""
    for test in get_tests():
        if test.id == test_id:
            return test
    return None

def save_test(test: Battle) -> None:
    """Save a test to the tests file."""
    global _tests
    tests = get_tests()
    
    # Update existing test or add new one
    updated = False
    for i, existing_test in enumerate(tests):
        if existing_test.id == test.id:
            tests[i] = test
            updated = True
            break
    
    if not updated:
        tests.append(test)
    
    # Update cache
    _tests = tests
    
    # Save to file
    with open("data/tests.json", "w") as f:
        json.dump({"tests": [t.model_dump() for t in tests]}, f, indent=4)

def delete_test(test_id: str) -> None:
    """Delete a test by ID."""
    global _tests
    tests = [t for t in get_tests() if t.id != test_id]
    
    # Update cache
    _tests = tests
    
    with open("data/tests.json", "w") as f:
        json.dump({"tests": [t.model_dump() for t in tests]}, f, indent=4) 