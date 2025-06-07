"""
Fix for the database module
"""
import database as db
import inspect

# Check if get_technology_stats exists
if not hasattr(db, "get_technology_stats"):
    # Print the attributes that are available
    print("Available functions in database module:")
    for attr in dir(db):
        if not attr.startswith("_"):
            print(f"- {attr}")
    
    # Try to inspect the source code to see if function exists but isn't being exposed
    try:
        source = inspect.getsource(db)
        print("\nChecking source code...")
        if "def get_technology_stats" in source:
            print("Function is defined in source but not exposed!")
        else:
            print("Function is not defined in the source code!")
    except:
        print("Could not inspect source code")
        
    # Add the function manually if needed
    print("\nAdding get_technology_stats function manually...")
    
    def get_technology_stats() -> list:
        """Get statistics for all technologies"""
        try:
            conn = db.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, count FROM technologies ORDER BY count DESC")
            
            stats = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return stats
        except Exception as e:
            print(f"Error getting technology stats: {e}")
            return []
    
    # Add the function to the module
    setattr(db, "get_technology_stats", get_technology_stats)
    print("Function added successfully!")
else:
    print("get_technology_stats function already exists in the module!")

# Now test the function
try:
    stats = db.get_technology_stats()
    print(f"\nFunction test result: {stats}")
except Exception as e:
    print(f"\nError calling function: {e}")

print("\nDatabase fix complete!")
