#!/usr/bin/env python3
import os
import random
import string

def generate_random_text(length=200):
    """
    Generate a random string of letters, digits, and spaces.
    """
    # Create a pool of characters to choose from
    characters = string.ascii_letters + string.digits + " " * 10  # More spaces for word-like feel
    return ''.join(random.choices(characters, k=length))

def create_dummy_data_directory(directory="dummy_data", num_files=10):
    """
    Create a directory and populate it with dummy text files.
    
    Each file is named dummy_file_#.txt and contains unique random text.
    """
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    print(f"Directory '{directory}' is ready.")

    for i in range(1, num_files + 1):
        file_path = os.path.join(directory, f"dummy_file_{i}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            # Write a header line
            f.write(f"Dummy File #{i}\n")
            f.write("-" * 40 + "\n")
            # Write some unique random text
            f.write(generate_random_text(300))
        print(f"Created file: {file_path}")

if __name__ == "__main__":
    # Change the number of files if desired
    create_dummy_data_directory(directory="dummy_data", num_files=10)