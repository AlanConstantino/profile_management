# Profile Management Tool

A simple cross-platform command-line tool to back up and restore configuration files and directories across multiple profiles. It uses a YAML manifest file to track which files and directories to manage, supports recursive copying, and allows you to explicitly specify a backup location for each profile.

## Features

- **Multiple Profiles:** Manage different sets of files (and directories) for various environments (e.g., `default`, `work`).
- **Recursive Backup/Restore:** Automatically copy entire directories (including subdirectories) while preserving their structure.
- **Custom Backup Locations:** Define a custom backup destination for each profile directly in the YAML manifest.
- **Cross-Platform:** Works on Unix-like systems (Linux, macOS) and Windows.

## Requirements

- Python 3.8+ (for `shutil.copytree` with `dirs_exist_ok=True`)
- [PyYAML](https://pyyaml.org/)  
  Install with:  
  ```bash
  pip install pyyaml
   ```

## Background

There isn’t a one–magic–solution, but the “best” approach that many have found is to build (or adapt) a manifest–driven system that uses your manifest as the single source of truth and then leverages a version control system (VCS) for backup and profile management. In practice, this means:

1. **Creating a Manifest File:**  
   Use a simple, human–readable file (for example, in YAML or JSON) that lists every file or repository you want to track. For each entry you might include:
   - The source file/directory path.
   - Any extra metadata (such as whether it’s already under version control).
   - Which profile(s) it belongs to.

2. **Backing Up with Version Control:**  
   Even if some of your files are not “source code”, you can still use a VCS (like Git) to track them. There are a couple of strategies here:
   - **Unified Repository with Submodules:** Put all your files (and repositories) into one “backup” repository. For files that are already under version control elsewhere, you can either leave them as is or add them as submodules.
   - **Separate Repositories:** For non–version–controlled files, have your tool copy or “import” them into a dedicated repository for backup.
   
   The key idea is that every time you make a change, your tool checks the manifest, gathers the files, and commits a snapshot.

3. **Supporting Multiple Profiles:**  
   The requirement that “switching profiles” shouldn’t lose changes is typically solved by having independent sets of tracked files. Common methods include:
   - **Branching:** Use one branch per profile. When you “switch” profiles, you check out the branch corresponding to that profile. Since each branch has its own commits, any changes made in one branch will be preserved when you switch away.
   - **Separate Directories/Worktrees:** Alternatively, you might use a tool like Git’s worktree feature or simply keep separate directories for each profile. Your manifest tells your tool where to “deploy” the files for the active profile.
   
   Either way, the manifest is used to know what files belong to what profile and a script or tool then “loads” (or deploys) that set. Changes in one profile are committed to its own branch/directory, so when you switch back the modifications are still there.

4. **Implementing the System:**  
   You can either write your own small command–line tool (in Python, Bash, etc.) that:
   - Reads the manifest.
   - Copies or symlinks files to a working location.
   - Commits any changes to the backup repository.
   - Switches between profiles (using branch switching, worktrees, or different directories).  
     
   Or, you can adapt an existing dotfiles management tool. Tools such as [chezmoi](https://www.chezmoi.io/) or [dotbot](https://github.com/anishathalye/dotbot) use manifest files to manage your configuration files. Although they are designed for dotfiles, they can easily be adapted to track arbitrary files and even support multiple “profiles” or sets.

### In Summary

The “best way” to solve your problem is to combine a simple manifest file with a VCS–backed deployment/back–up system that supports multiple profiles. This might look like:

- A manifest (YAML/JSON) listing all files/repositories and their associated profiles.
- A tool that, when invoked, reads the manifest, copies/symlinks files into place, and commits any changes (using Git, for example).
- A profile–switching mechanism (via Git branches, worktrees, or separate directories) so that each profile’s state is independent and switching does not lose uncommitted changes.

This approach gives you a unified, versioned backup for everything you need to track, and lets users load different profiles without fear of losing their changes.

## Configuration

Create a manifest.yaml file in the same directory as profile_manager.py. This YAML file defines your profiles, the files and directories you wish to manage, and optionally the backup locations for each profile.

Example manifest.yaml:

```yaml
profiles:
  default:
    # Optional: Define a custom backup location for this profile.
    backup_location: "~/backups/default_profile"
    files:
      - target: "~/bashrc"
      - target: "~/vimrc"
      - target: "/Users/yourusername/Code/profile_management/dummy_data"
  work:
    backup_location: "~/backups/work_profile"
    files:
      - target: "~/Documents/work_config.ini"
      - target: "/Users/yourusername/Projects/work_profile"
```

- profiles: A mapping of profile names to their configuration.
- backup_location (Optional): If specified, the tool will back up and restore files for that profile at this location. If not provided, the tool defaults to an internal location:
  - On Unix-like systems: ~/.mytool/profiles/<profile>
  - On Windows: A subdirectory in your APPDATA directory.
- files: A list of items to manage. Each item must contain a target key that points to the file or directory you wish to track. Directories are backed up recursively.

Usage

Run the tool using Python from a terminal or command prompt. Below are the available commands.

Command-Line Options
	•	backup:
Backs up the current active profile.

```bash
python profile_manager.py backup
```

#### restore:

Restores files for the current active profile from the backup location.

```bash
python profile_manager.py restore
```

#### switch:

Switches to a specified profile. This command automatically backs up the current profile, sets the new profile as active, and restores its files.

```bash
python profile_manager.py switch --profile work
```

#### list:

Lists all available profiles defined in the manifest.

```bash
python profile_manager.py list
```

#### current:

Displays the current active profile.

```bash
python profile_manager.py current
```

### Examples

1.	Backup the Active Profile:

Ensure that your desired profile is active (the tool uses an internal file to track the current profile). Then run:

```bash
python profile_manager.py backup
```

This will copy each file or directory defined in the active profile to its specified backup location (or the default internal location).

2.	Restore the Active Profile:

To restore files for the active profile from its backup:

```bash
python profile_manager.py restore
```

This will copy each file or directory from the backup location back to its original location.

3.	Switch to the “work” Profile:

To switch to the work profile (which will also back up your current profile before switching):

```bash
python profile_manager.py switch --profile work
```

This will back up the current profile, switch to the work profile, and restore the files for the work profile.

This command:
	•	Backs up the currently active profile.
	•	Sets work as the active profile.
	•	Restores files and directories for the work profile from its backup location.

4.	List Available Profiles:

To see which profiles are defined in your manifest:

```bash
python profile_manager.py list
```

This will display a list of all profiles defined in the manifest.

5.	Show the Current Active Profile:

To print the name of the current active profile:

```bash
python profile_manager.py current
```

This will output the name of the currently active profile.

### Additional Information

#### Recursive Operation:

When a directory is specified as a target, the tool uses os.walk() to recursively copy all files (and preserves subdirectory structure) during backup and restore.

#### Cross-Platform Paths:

The tool handles Unix-like and Windows paths automatically. Use the tilde (~) to reference the home directory.

### Contributing

Contributions, bug fixes, and feature requests are welcome. Feel free to open an issue or submit a pull request.

### License

This project is licensed under the MIT License.
