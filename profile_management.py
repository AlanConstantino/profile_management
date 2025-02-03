#!/usr/bin/env python3
"""
A cross-platform profile manager.

Usage examples:
  python profile_manager.py backup
    -> Back up (i.e. save) the current active profile (copies each file from its target location
       to an internal backup folder).

  python profile_manager.py restore
    -> Restore (i.e. load) the current active profile (copies each file from the backup folder to the target).

  python profile_manager.py switch --profile work
    -> Save the current profile, then switch to the “work” profile (restoring its files).

  python profile_manager.py list
    -> List available profiles.

  python profile_manager.py current
    -> Show the current active profile.

Make sure you have PyYAML installed (e.g., pip install pyyaml).
"""

import os
import sys
import argparse
import yaml
import shutil

# --- Cross–platform support for storing tool data ---
# On Windows, use the APPDATA directory; on Unix–like systems, use the home directory.
if sys.platform.startswith("win"):
    # On Windows, default to the APPDATA folder (or fallback to home if APPDATA is not set)
    APPDATA = os.getenv("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    MYTOOL_DIR = os.path.join(APPDATA, "mytool")
else:
    HOME = os.path.expanduser("~")
    MYTOOL_DIR = os.path.join(HOME, ".mytool")

CURRENT_PROFILE_FILE = os.path.join(MYTOOL_DIR, "current_profile.txt")
PROFILES_DIR = os.path.join(MYTOOL_DIR, "profiles")


def load_manifest(manifest_path):
    """Load and return the manifest from a YAML file."""
    with open(manifest_path, "r") as f:
        return yaml.safe_load(f)


def get_active_profile(manifest):
    """Determine the active profile.
    
    This checks for a saved active profile; if none exists, it defaults to "default"
    if present, or the first defined profile.
    """
    if os.path.exists(CURRENT_PROFILE_FILE):
        with open(CURRENT_PROFILE_FILE, "r") as f:
            profile = f.read().strip()
            if profile in manifest.get("profiles", {}):
                return profile

    profiles = list(manifest.get("profiles", {}).keys())
    if "default" in profiles:
        return "default"
    elif profiles:
        return profiles[0]
    else:
        raise ValueError("No profiles defined in manifest.")


def set_active_profile(profile):
    """Save the active profile name."""
    os.makedirs(MYTOOL_DIR, exist_ok=True)
    with open(CURRENT_PROFILE_FILE, "w") as f:
        f.write(profile)


def backup_profile(manifest, profile):
    """Backup (save) the current live files for the given profile.
    
    For each file in the profile, this function copies the file from its target location
    into the profile's backup directory (under the tool's data folder).
    """
    print(f"Backing up profile: {profile}")
    profile_data = manifest.get("profiles", {}).get(profile, {})
    files = profile_data.get("files", [])
    profile_backup_dir = os.path.join(PROFILES_DIR, profile)
    os.makedirs(profile_backup_dir, exist_ok=True)

    for entry in files:
        target = os.path.expanduser(entry["target"])
        # For simplicity, we use the basename of the target file for storage.
        filename = os.path.basename(target)
        backup_path = os.path.join(profile_backup_dir, filename)
        if os.path.exists(target):
            try:
                shutil.copy2(target, backup_path)
                print(f"  Copied {target} -> {backup_path}")
            except Exception as e:
                print(f"  Error copying {target}: {e}")
        else:
            print(f"  WARNING: Target file {target} does not exist; skipping.")


def restore_profile(manifest, profile):
    """Restore (load) the backup for the given profile.
    
    For each file in the profile, this function copies the backup copy from the profile's backup
    directory to its target location.
    """
    print(f"Restoring profile: {profile}")
    profile_data = manifest.get("profiles", {}).get(profile, {})
    files = profile_data.get("files", [])
    profile_backup_dir = os.path.join(PROFILES_DIR, profile)

    for entry in files:
        target = os.path.expanduser(entry["target"])
        filename = os.path.basename(target)
        backup_path = os.path.join(profile_backup_dir, filename)
        if os.path.exists(backup_path):
            # Make sure the target directory exists.
            os.makedirs(os.path.dirname(target), exist_ok=True)
            try:
                shutil.copy2(backup_path, target)
                print(f"  Restored {backup_path} -> {target}")
            except Exception as e:
                print(f"  Error restoring {target}: {e}")
        else:
            print(f"  WARNING: Backup file {backup_path} does not exist; cannot restore {target}.")


def switch_profile(manifest, new_profile):
    """Switch from the current profile to a new profile.
    
    This backs up the current profile and then restores the new profile.
    """
    current_profile = get_active_profile(manifest)
    if current_profile == new_profile:
        print(f"Already using profile '{new_profile}'.")
        return

    print(f"Switching from profile '{current_profile}' to profile '{new_profile}'.")

    # Backup current profile.
    backup_profile(manifest, current_profile)
    # Set the new active profile.
    set_active_profile(new_profile)
    # Restore the new profile.
    restore_profile(manifest, new_profile)
    print(f"Switched to profile '{new_profile}'.")


def list_profiles(manifest):
    """List all profiles defined in the manifest."""
    profiles = manifest.get("profiles", {})
    print("Available profiles:")
    for p in profiles:
        print(f" - {p}")


def main():
    parser = argparse.ArgumentParser(description="Cross–platform Profile Manager Tool")
    parser.add_argument(
        "command",
        choices=["backup", "restore", "switch", "list", "current"],
        help="Command to execute",
    )
    parser.add_argument("--profile", help="Profile name (required for switch command)")
    parser.add_argument(
        "--manifest",
        default="manifest.yaml",
        help="Path to manifest file (default: manifest.yaml)",
    )
    args = parser.parse_args()

    try:
        manifest = load_manifest(args.manifest)
    except Exception as e:
        print(f"Error loading manifest file: {e}")
        return

    if args.command == "backup":
        current = get_active_profile(manifest)
        backup_profile(manifest, current)
    elif args.command == "restore":
        current = get_active_profile(manifest)
        restore_profile(manifest, current)
    elif args.command == "switch":
        if not args.profile:
            print("Error: Please specify a profile with --profile.")
            return
        if args.profile not in manifest.get("profiles", {}):
            print(f"Error: Profile '{args.profile}' not found in manifest.")
            return
        switch_profile(manifest, args.profile)
    elif args.command == "list":
        list_profiles(manifest)
    elif args.command == "current":
        current = get_active_profile(manifest)
        print(f"Current active profile: {current}")


if __name__ == "__main__":
    main()
