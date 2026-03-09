import json
import glob
import os
import re
from datetime import datetime

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: BeautifulSoup is required to parse HTML.")
    print("Please install it by running: pip install beautifulsoup4")
    exit()

# --- Configuration ---
base_dir = os.path.dirname(os.path.abspath(__file__))
# Search for HTML files instead of JSON
pattern = os.path.join(base_dir, "message_*.html")
input_filenames = sorted(glob.glob(pattern))
output_filename = os.path.join(base_dir, "combined_messages.json")

# --- Main Logic ---
if not input_filenames:
    print(f"Error: No HTML message files (e.g., 'message_1.html') found in {base_dir}.")
else:
    print(f"Found {len(input_filenames)} HTML files to parse and combine.")

    all_messages = []

    for filepath in input_filenames:
        print(f"Reading {filepath}...")
        with open(filepath, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, 'html.parser')

            # Instagram HTML wraps every message in this specific class string
            message_blocks = soup.find_all('div', class_='pam _3-95 _2ph- _a6-g uiBoxWhite noborder')

            for block in message_blocks:
                msg_obj = {}

                # 1. Extract Sender Name
                sender_tag = block.find('h2')
                if not sender_tag:
                    continue
                sender_text = sender_tag.get_text(strip=True)
                
                # Skip HTML-specific metadata blocks
                if sender_text.startswith("Participants:") or sender_text == "Group photo" or sender_text.startswith("Group Invite Link:"):
                    continue
                
                msg_obj['sender_name'] = sender_text

                # 2. Extract Timestamp
                time_tag = block.find('div', class_='_3-94 _a6-o')
                if time_tag:
                    time_str = time_tag.get_text(strip=True)
                    try:
                        # Convert "Mar 08, 2026 2:15 pm" to a timestamp in milliseconds
                        dt = datetime.strptime(time_str, "%b %d, %Y %I:%M %p")
                        msg_obj['timestamp_ms'] = int(dt.timestamp() * 1000)
                    except ValueError:
                        msg_obj['timestamp_ms'] = 0

                # 3. Extract Content & Attachments
                content_div = block.find('div', class_='_3-95 _a6-p')
                if content_div:
                    inner_divs = content_div.find_all('div', recursive=False)
                    if inner_divs:
                        main_wrapper = inner_divs[0]
                        child_divs = main_wrapper.find_all('div', recursive=False)

                        # Extract text
                        if len(child_divs) >= 2:
                            text_content = child_divs[1].get_text(strip=True)
                            
                            # Filter out automated Instagram system text that clutter the chat
                            ignore_phrases = ["sent an attachment.", "video chat", "liked a message", "sent a doodle."]
                            is_action = any(phrase in text_content for phrase in ignore_phrases)

                            if text_content and not is_action:
                                msg_obj['content'] = text_content

                        # Look for links (GIFs, Instagram reels/shares)
                        links = main_wrapper.find_all('a')
                        for link in links:
                            href = link.get('href', '')
                            if 'giphy.com' in href:
                                msg_obj['gifs'] = [{'link': href}]
                            elif 'instagram.com' in href and not msg_obj.get('content'):
                                msg_obj['share'] = {'link': href}

                        # Look for Photos
                        imgs = main_wrapper.find_all('img')
                        for img in imgs:
                            src = img.get('src', '')
                            if src and not src.endswith("Instagram-Logo.png"):
                                msg_obj['photos'] = msg_obj.get('photos', []) + [{'uri': src}]

                        # Look for Videos
                        vids = main_wrapper.find_all('video')
                        for vid in vids:
                            src = vid.get('src', '')
                            if src:
                                msg_obj['videos'] = msg_obj.get('videos', []) + [{'uri': src}]

                # 4. Extract Reactions
                reaction_list = block.find('ul', class_='_a6-q')
                if reaction_list:
                    reactions = []
                    for li in reaction_list.find_all('li'):
                        react_text = li.get_text(strip=True)
                        
                        # Separate the emoji from the user's name (e.g., "❤aiden kim")
                        match = re.match(r'^([^\w\s]+)(.*)', react_text)
                        if match:
                            reaction_char = match.group(1).strip()
                            actor = match.group(2).strip()
                            reactions.append({"reaction": reaction_char, "actor": actor})
                    
                    if reactions:
                        msg_obj['reactions'] = reactions

                # Validate it's an actual message block before adding
                if msg_obj.get('content') or msg_obj.get('photos') or msg_obj.get('videos') or msg_obj.get('gifs') or msg_obj.get('share'):
                    all_messages.append(msg_obj)

    print("\nSorting all messages chronologically...")
    all_messages.sort(key=lambda msg: msg.get("timestamp_ms", 0), reverse=False)

    final_json_structure = {"messages": all_messages}

    # Write identical JSON format for the parser
    try:
        with open(output_filename, "w", encoding="utf-8") as outfile:
            json.dump(final_json_structure, outfile, indent=2)
        print(f"\nSuccess! Extracted data from HTML and generated '{output_filename}'.")
        print(f"Total messages combined: {len(all_messages)}")
    except Exception as e:
        print(f"An error occurred while writing the file: {e}")