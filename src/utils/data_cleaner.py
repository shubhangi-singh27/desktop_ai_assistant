from pathlib import Path
import shutil

def clear_all_data(confirm=True):
    data_dir = Path("data")

    if not data_dir.exists():
        print("Data directory doesn't exist.")
        return True
    
    if confirm:
        print("\n" + "="*60)
        print("WARNING: This will delete all data in the data directory.")
        print("="*60)
        response = input("Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("Deletion cancelled.")
            return False

        print("="*60 + "\n")

    for subdir in ['events', 'screenshots', 'audio']:
        path = data_dir/subdir
        if path.exists():
            try:
                shutil.rmtree(path)
                print(f"Deleted {subdir} directory.")
            except Exception as e:
                print(f"Error deleting {subdir} directory: {e}")

    deleted_files = 0
    for file in data_dir.glob("*.*"):
        if file.is_file():
            try:
                file.unlink()
                deleted_files += 1
            except Exception as e:
                print(f"Error deleting {file.name}: {e}")
    
    if deleted_files > 0:
        print(f"Deleted {deleted_files} files.")

    print("All data cleared.")
    return True