"""
Debug script to check if database module is loading correctly
"""
import importlib
import database as db

# Reload the module to ensure we get the latest version
importlib.reload(db)

# Print out all functions in the module
print("Available functions in database module:")
for item in dir(db):
    if not item.startswith("_"):  # Skip private methods
        print(f"- {item}")

# Specifically check if get_technology_stats exists
if hasattr(db, "get_technology_stats"):
    print("\nget_technology_stats function exists!")
    # Test the function
    try:
        stats = db.get_technology_stats()
        print(f"Function returned: {stats}")
    except Exception as e:
        print(f"Error calling function: {e}")
else:
    print("\nERROR: get_technology_stats function does not exist in the module!")

print("\nChecking database file:")
import os
print(f"Database file exists: {os.path.exists(db.DB_PATH)}")
