import json
import glob
import os

# --- Configuration ---
base_dir = os.path.dirname(os.path.abspath(__file__))
# This pattern finds any file with "combined_messages" in the name
pattern = os.path.join(base_dir, "*combined_messages*.json")
input_filenames = sorted(glob.glob(pattern))
output_filename = os.path.join(base_dir, "master_combined_messages.json")

# --- Main Logic ---
if not input_filenames:
    print(f"Error: No files matching '*combined_messages*.json' found in {base_dir}.")
    exit()

print(f"Found {len(input_filenames)} files to merge: {[os.path.basename(f) for f in input_filenames]}")

unique_messages = {}
unique_participants = set()

for filepath in input_filenames:
    print(f"Processing {os.path.basename(filepath)}...")
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
            
            # 1. Merge Participants
            for participant in data.get("participants", []):
                name = participant.get("name")
                if name:
                    unique_participants.add(name)

            # 2. Merge and Deduplicate Messages
            messages = data.get("messages", [])
            for msg in messages:
                # Create a unique key based on exact time and sender
                timestamp = msg.get("timestamp_ms", 0)
                sender = msg.get("sender_name", "Unknown")
                
                msg_key = f"{timestamp}_{sender}"
                
                if msg_key not in unique_messages:
                    unique_messages[msg_key] = msg
                else:
                    # If the message exists, keep the richer version (e.g., if a reaction was added in the newer export)
                    existing_len = len(json.dumps(unique_messages[msg_key]))
                    new_len = len(json.dumps(msg))
                    
                    if new_len > existing_len:
                        unique_messages[msg_key] = msg

    except Exception as e:
        print(f"Error processing {filepath}: {e}")

# Rebuild the final lists
final_participants = [{"name": name} for name in unique_participants]
final_messages = list(unique_messages.values())

print("\nSorting final merged messages chronologically...")
# Sort chronologically (oldest first) or reverse=True for newest first, depending on your preference
final_messages.sort(key=lambda msg: msg.get("timestamp_ms", 0), reverse=False)

# Construct the final JSON structure
final_json_structure = {
    "participants": final_participants,
    "messages": final_messages
}

# Write to the new master file
try:
    with open(output_filename, "w", encoding="utf-8") as outfile:
        json.dump(final_json_structure, outfile, indent=2)
    print(f"\nSuccess! Deduplicated data saved to '{os.path.basename(output_filename)}'.")
    print(f"Total unique participants: {len(final_participants)}")
    print(f"Total unique messages combined: {len(final_messages)}")
except Exception as e:
    print(f"An error occurred while writing the file: {e}")