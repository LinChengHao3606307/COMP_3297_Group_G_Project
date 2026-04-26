import os
import shutil

def clean_migrations_folders():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning root directory: {base_dir}")
    print("Recursively searching for all migrations folders...\n")

    migration_paths = []

    for root, dirs, files in os.walk(base_dir):
        if "migrations" in dirs:
            mig_path = os.path.join(root, "migrations")
            migration_paths.append(mig_path)

    if not migration_paths:
        print("No migrations folders found!")
        return

    print("Found the following migrations folders:")
    for path in migration_paths:
        print(f" - {path}")

    confirm = input("\nClear the contents of these folders? (Keep __init__.py only) [y/N]: ")
    if confirm.lower() != "y":
        print("Cleanup cancelled")
        return

    print("\nStarting cleanup...")

    for mig_folder in migration_paths:
        for item in os.listdir(mig_folder):
            item_path = os.path.join(mig_folder, item)

            if item == "__init__.py":
                continue

            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        print(f"Cleaned: {mig_folder}")

    print(f"Cleanup complete")


if __name__ == "__main__":
    clean_migrations_folders()