#!/usr/bin/env python3
"""
A cross-platform Profile Manager Tool with recursive backup/restore and
explicit backup locations defined in the YAML manifest.

Usage examples:
  python profile_manager.py backup
    -> Back up (i.e. save) the current active profile. This copies each file or directory
       from its target location to the specified backup location (if defined in the manifest)
       or to the default internal backup folder.

  python profile_manager.py restore
    -> Restore (i.e. load) the current active profile by copying backup data into the target locations.

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
if sys.platform.startswith("win"):
    # On Windows, use the APPDATA directory (or fallback to a subfolder in home)
    APPDATA = os.getenv("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    MYTOOL_DIR = os.path.join(APPDATA, "mytool")
else:
    HOME = os.path.expanduser("~")
    MYTOOL_DIR = os.path.join(HOME, ".mytool")

CURRENT_PROFILE_FILE = os.path.join(MYTOOL_DIR, "current_profile.txt")
# Default internal location if no backup_location is specified in the manifest.
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


def get_backup_dir_for_profile(profile_data, profile_name):
    """
    Return the backup directory for the profile.
    If the profile defines a 'backup_location' in the manifest, that path (expanded) is used.
    Otherwise, use the default internal location (MYTOOL_DIR/profiles/<profile>).
    """
    if 'backup_location' in profile_data:
        backup_dir = os.path.expanduser(profile_data['backup_location'])
    else:
        backup_dir = os.path.join(PROFILES_DIR, profile_name)
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def backup_target(target, backup_dir):
    """
    Back up the given target (a file or directory) into backup_dir.

    - If target is a file, it is copied to backup_dir using its basename.
    - If target is a directory, its contents are recursively copied to a subdirectory
      in backup_dir with the same basename as the target.
    """
    target = os.path.expanduser(target)
    if os.path.isfile(target):
        filename = os.path.basename(target)
        backup_path = os.path.join(backup_dir, filename)
        try:
            shutil.copy2(target, backup_path)
            print(f"  Copied file {target} -> {backup_path}")
        except Exception as e:
            print(f"  Error copying file {target}: {e}")
    elif os.path.isdir(target):
        # Create a subdirectory in backup_dir with the same basename as target.
        dest_root = os.path.join(backup_dir, os.path.basename(target))
        for root, _, files in os.walk(target):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, target)
                dest_path = os.path.join(dest_root, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                try:
                    shutil.copy2(file_path, dest_path)
                    print(f"  Copied file {file_path} -> {dest_path}")
                except Exception as e:
                    print(f"  Error copying file {file_path}: {e}")
    else:
        print(f"  WARNING: Target {target} does not exist; skipping.")


def restore_target(target, backup_dir):
    """
    Restore the given target from its backup located in backup_dir.

    - If the backup was a file, it is copied to target.
    - If the backup was a directory, its contents are recursively copied back to target.
    """
    target = os.path.expanduser(target)
    backup_source = os.path.join(backup_dir, os.path.basename(target))
    if not os.path.exists(backup_source):
        print(f"  WARNING: Backup source {backup_source} does not exist; cannot restore {target}.")
        return

    if os.path.isfile(backup_source):
        os.makedirs(os.path.dirname(target), exist_ok=True)
        try:
            shutil.copy2(backup_source, target)
            print(f"  Restored file {backup_source} -> {target}")
        except Exception as e:
            print(f"  Error restoring file {target}: {e}")
    elif os.path.isdir(backup_source):
        try:
            os.makedirs(target, exist_ok=True)
            shutil.copytree(backup_source, target, dirs_exist_ok=True)
            print(f"  Restored directory {backup_source} -> {target}")
        except Exception as e:
            print(f"  Error restoring directory {target}: {e}")


def backup_profile(manifest, profile):
    """Back up the current live files (and directories) for the given profile."""
    print(f"Backing up profile: {profile}")
    profile_data = manifest.get("profiles", {}).get(profile, {})
    entries = profile_data.get("files", [])
    backup_dir = get_backup_dir_for_profile(profile_data, profile)

    for entry in entries:
        target = entry["target"]
        backup_target(target, backup_dir)


def restore_profile(manifest, profile):
    """Restore the backup for the given profile to the live target locations."""
    print(f"Restoring profile: {profile}")
    profile_data = manifest.get("profiles", {}).get(profile, {})
    entries = profile_data.get("files", [])
    backup_dir = get_backup_dir_for_profile(profile_data, profile)

    for entry in entries:
        target = entry["target"]
        restore_target(target, backup_dir)


def switch_profile(manifest, new_profile):
    """Switch from the current profile to a new profile."""
    current_profile = get_active_profile(manifest)
    if current_profile == new_profile:
        print(f"Already using profile '{new_profile}'.")
        return

    print(f"Switching from profile '{current_profile}' to profile '{new_profile}'.")
    backup_profile(manifest, current_profile)
    set_active_profile(new_profile)
    restore_profile(manifest, new_profile)
    print(f"Switched to profile '{new_profile}'.")


def list_profiles(manifest):
    """List all profiles defined in the manifest."""
    profiles = manifest.get("profiles", {})
    print("Available profiles:")
    for p in profiles:
        print(f" - {p}")


def main():
    parser = argparse.ArgumentParser(description="Cross–platform Profile Manager Tool with Explicit Backup Locations")
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