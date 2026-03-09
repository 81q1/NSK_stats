import json
import glob
import os

# --- Configuration ---
# Make the script search for files in the same directory as this script.
# This avoids 'no matching filenames' when the script is run from another CWD.
base_dir = os.path.dirname(os.path.abspath(__file__))
pattern = os.path.join(base_dir, "message_*.json")
input_filenames = sorted(glob.glob(pattern))
output_filename = os.path.join(base_dir, "combined_messages.json")

# --- Main Logic ---
if not input_filenames:
    print(f"Error: No message files (e.g., 'message_1.json') found in {base_dir}.")
else:
    print(f"Found {len(input_filenames)} files to combine.")

    # This list will store every message object from all files
    all_messages = []
    
    # We'll take the metadata (participants, title, etc.) from the first file
    final_json_structure = None

    for filepath in input_filenames:
        try:
            print(f"Reading {filepath}...")
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)

                # If this is the first file, save its structure
                if final_json_structure is None:
                    final_json_structure = data
                
                # Add the messages from the current file to our master list
                all_messages.extend(data.get("messages", []))
        
        except FileNotFoundError:
            print(f"Warning: Could not find the file {filepath}. Skipping.")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {filepath}. It might be corrupted. Skipping.")
        except Exception as e:
            print(f"An unexpected error occurred with {filepath}: {e}")

    if final_json_structure:
        print("\nCombining and sorting all messages by date...")
        
        # Sort the master list of messages by timestamp (oldest first)
        # The 'reverse=True' is because Instagram's timestamps are newest first.
        # If your chat appears backwards, change it to reverse=False.
        all_messages.sort(key=lambda msg: msg.get("timestamp_ms", 0), reverse=True)
        
        # Replace the (now empty) message list in our final structure with the sorted one
        final_json_structure["messages"] = all_messages
        
        # Write the combined data to the new file
        try:
            with open(output_filename, "w", encoding="utf-8") as outfile:
                # Use indent=2 for a nicely formatted, human-readable file
                json.dump(final_json_structure, outfile, indent=2)
            print(f"\nSuccess! All messages have been combined into '{output_filename}'.")
            print(f"Total messages combined: {len(all_messages)}")
        except Exception as e:
            print(f"An error occurred while writing the file: {e}")