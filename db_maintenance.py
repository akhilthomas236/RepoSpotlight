"""
Database maintenance utility for GitHub Project Showcase
"""
import os
import sqlite3
import shutil

DB_PATH = "github_projects.db"
WAL_PATH = "github_projects.db-wal"
SHM_PATH = "github_projects.db-shm"
BACKUP_DIR = ".db_backups"

def backup_database():
    """Backup the database files"""
    # Create backup directory if it doesn't exist
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    # Get timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup main database file
    if os.path.exists(DB_PATH):
        backup_path = os.path.join(BACKUP_DIR, f"{timestamp}_{DB_PATH}")
        shutil.copy2(DB_PATH, backup_path)
        print(f"Database backed up to {backup_path}")
    
    # Backup WAL file if it exists
    if os.path.exists(WAL_PATH):
        backup_path = os.path.join(BACKUP_DIR, f"{timestamp}_{os.path.basename(WAL_PATH)}")
        shutil.copy2(WAL_PATH, backup_path)
        print(f"WAL file backed up to {backup_path}")
    
    # Backup SHM file if it exists
    if os.path.exists(SHM_PATH):
        backup_path = os.path.join(BACKUP_DIR, f"{timestamp}_{os.path.basename(SHM_PATH)}")
        shutil.copy2(SHM_PATH, backup_path)
        print(f"SHM file backed up to {backup_path}")

def vacuum_database():
    """Vacuum the database to optimize it"""
    try:
        print("Vacuuming database...")
        conn = sqlite3.connect(DB_PATH)
        conn.execute("VACUUM")
        conn.close()
        print("Database vacuum completed successfully")
        return True
    except Exception as e:
        print(f"Error vacuuming database: {e}")
        return False

def checkpoint_wal():
    """Force a checkpoint of the WAL file"""
    try:
        print("Forcing WAL checkpoint...")
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA wal_checkpoint(FULL)")
        conn.close()
        print("WAL checkpoint completed")
        return True
    except Exception as e:
        print(f"Error checkpointing WAL: {e}")
        return False

def reset_journal_mode():
    """Reset journal mode to DELETE (from WAL)"""
    try:
        print("Resetting journal mode to DELETE...")
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode = DELETE")
        conn.close()
        print("Journal mode reset")
        return True
    except Exception as e:
        print(f"Error resetting journal mode: {e}")
        return False

def set_wal_mode():
    """Set journal mode to WAL"""
    try:
        print("Setting journal mode to WAL...")
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.close()
        print("Journal mode set to WAL")
        return True
    except Exception as e:
        print(f"Error setting WAL mode: {e}")
        return False

def clean_wal_files():
    """Clean up WAL and SHM files"""
    try:
        print("Cleaning WAL files...")
        # First try to checkpoint
        checkpoint_wal()
        
        # Then reset journal mode
        reset_journal_mode()
        
        # Delete WAL file if it exists
        if os.path.exists(WAL_PATH):
            os.remove(WAL_PATH)
            print(f"Removed {WAL_PATH}")
            
        # Delete SHM file if it exists
        if os.path.exists(SHM_PATH):
            os.remove(SHM_PATH)
            print(f"Removed {SHM_PATH}")
        
        # Reset to WAL mode
        set_wal_mode()
        
        return True
    except Exception as e:
        print(f"Error cleaning WAL files: {e}")
        return False

def fix_locked_database():
    """Try to fix a locked database"""
    print("Attempting to fix locked database...")
    
    # First backup the database
    backup_database()
    
    # Try vacuum
    vacuum_result = vacuum_database()
    
    # Clean WAL files
    wal_result = clean_wal_files()
    
    if vacuum_result and wal_result:
        print("Database lock issues should be resolved")
        return True
    else:
        print("Could not fully resolve database lock issues")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "backup":
            backup_database()
        elif command == "vacuum":
            vacuum_database()
        elif command == "checkpoint":
            checkpoint_wal()
        elif command == "reset":
            reset_journal_mode()
        elif command == "wal":
            set_wal_mode()
        elif command == "clean":
            clean_wal_files()
        elif command == "fix":
            fix_locked_database()
        else:
            print("Unknown command")
            print("Available commands: backup, vacuum, checkpoint, reset, wal, clean, fix")
    else:
        print("Please specify a command")
        print("Available commands: backup, vacuum, checkpoint, reset, wal, clean, fix")
