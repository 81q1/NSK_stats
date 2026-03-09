import json
from datetime import datetime

def get_message_representation(message):
    if message.get("content"): return message["content"]
    if message.get("photos"): return f"[Photo: {message['photos'][0]['uri']}]"
    if message.get("videos"): return f"[Video: {message['videos'][0]['uri']}]"
    if message.get("gifs"): return f"[GIF: {message['gifs'][0].get('link', 'N/A')}]"
    if message.get("share"): return f"[Shared Link: {message['share'].get('link', 'N/A')}]"
    if message.get("audio_files"): return f"[Audio: {message['audio_files'][0]['uri']}]"
    return "[Non-text message]"

def generate_report(messages_list, section_title, like_cutoff, message_cutoff):
    like_counts, message_counts, reaction_giver_counts = {}, {}, {}
    min_timestamp_ms, max_timestamp_ms = float('inf'), float('-inf')
    max_reactions, most_reacted_message, most_reacted_sender = 0, None, None
    top_messages, output_lines = [], []

    output_lines.append(f"=== SECTION: {section_title} ===")

    if not messages_list:
        output_lines.append("No messages found in this time period.\n")
        return output_lines

    for message in messages_list:
        sender = message.get("sender_name", "Unknown Sender")
        if sender == "Meta AI":
            continue

        reactions = message.get("reactions", [])
        for reaction in reactions:
            actor = reaction.get("actor")
            if actor == "Meta AI":
                continue
            if actor: reaction_giver_counts[actor] = reaction_giver_counts.get(actor, 0) + 1
        
        message_counts[sender] = message_counts.get(sender, 0) + 1
        
        content, num_reactions = get_message_representation(message), len(reactions)
        timestamp_ms = message.get("timestamp_ms")
        if timestamp_ms: min_timestamp_ms, max_timestamp_ms = min(min_timestamp_ms, timestamp_ms), max(max_timestamp_ms, timestamp_ms)
        if num_reactions > 0: like_counts[sender] = like_counts.get(sender, 0) + num_reactions
        if num_reactions > max_reactions: max_reactions, most_reacted_message, most_reacted_sender = num_reactions, content, sender
        if num_reactions > 3: top_messages.append((sender, content, num_reactions))

    user_multipliers = {}
    all_users = list(message_counts.keys())
    giver_counts_full = {user: reaction_giver_counts.get(user, 0) for user in all_users}
    
    if giver_counts_full:
        sorted_givers = sorted(giver_counts_full.items(), key=lambda item: item[1])
        num_users = len(sorted_givers)
        p10_index, p30_index, p70_index, p90_index = int(num_users * 0.1), int(num_users * 0.3), int(num_users * 0.7), int(num_users * 0.9)
        for i, (user, count) in enumerate(sorted_givers):
            if i < p10_index: user_multipliers[user] = 0.8
            elif i < p30_index: user_multipliers[user] = 0.9
            elif i < p70_index: user_multipliers[user] = 1.0
            elif i < p90_index: user_multipliers[user] = 1.1
            else: user_multipliers[user] = 1.2
    
    start_date = datetime.fromtimestamp(min_timestamp_ms / 1000).strftime('%B %d, %Y') if min_timestamp_ms != float('inf') else "N/A"
    end_date = datetime.fromtimestamp(max_timestamp_ms / 1000).strftime('%B %d, %Y') if max_timestamp_ms != float('-inf') else "N/A"
    output_lines.extend([f"--- Chat History Time Period ---", f"Messages from: {start_date} to {end_date}\n"])
    
    reaction_leaderboard_data = []
    for sender, total_messages in message_counts.items():
        total_likes = like_counts.get(sender, 0)
        if total_likes < like_cutoff or total_messages < message_cutoff:
            continue
        lpm = total_likes / total_messages if total_messages > 0 else 0
        multiplier = user_multipliers.get(sender, 1.0)
        adjusted_lpm = lpm * multiplier
        reaction_leaderboard_data.append({"name": sender, "likes": total_likes, "lpm": lpm, "adjusted_lpm": adjusted_lpm})
    
    sorted_reaction_leaderboard = sorted(reaction_leaderboard_data, key=lambda x: x['adjusted_lpm'], reverse=True)
    output_lines.append("--- Reaction Leaderboard ---")
    for rank, data in enumerate(sorted_reaction_leaderboard, 1):
        output_lines.append(f"{rank}. {data['name']}: {data['likes']} Likes | {data['lpm']:.2f} LPM | {data['adjusted_lpm']:.2f} Adjusted LPM")

    top_giver_name, top_giver_count = "N/A", 0
    if reaction_giver_counts:
        top_giver_name = max(reaction_giver_counts, key=reaction_giver_counts.get)
        top_giver_count = reaction_giver_counts[top_giver_name]
    output_lines.extend(["\n--- Top Reaction Giver ---", f"{top_giver_name} gave out the most reactions: {top_giver_count}"])
    
    output_lines.append("\n--- Reaction Giver Leaderboard ---")
    sorted_givers_desc = sorted(reaction_giver_counts.items(), key=lambda item: item[1], reverse=True)
    for rank, (name, count) in enumerate(sorted_givers_desc, 1):
        output_lines.append(f"{rank}. {name}: {count} reactions given")

    output_lines.append("\n--- Most Reacted Message ---")
    output_lines.extend([f"Sender: {most_reacted_sender}", f"Message: {most_reacted_message}", f"Number of Reactions: {max_reactions}"])
    output_lines.append("\n--- Messages with More Than 3 Reactions ---")
    top_messages.sort(key=lambda item: item[2], reverse=True)
    for name, msg, count in top_messages:
        output_lines.append(f"{name}: {msg} | Reactions: {count}")

    return output_lines

try:
    with open("master_combined_messages.json", "r", encoding="utf-8") as file:
        json_data = json.load(file)

    messages_list = json_data["messages"]
    
    # 1. Complete History Report
    complete_report = generate_report(messages_list, "Complete History", like_cutoff=10, message_cutoff=500)
    
    # 2. Since September 19th Report
    # Modify the year here if needed
    cutoff_date = datetime(2025, 9, 19) 
    cutoff_ms = int(cutoff_date.timestamp() * 1000)
    
    recent_messages = [msg for msg in messages_list if msg.get("timestamp_ms", 0) >= cutoff_ms]
    
    # Reduced cutoffs for the shorter timeframe to ensure people still make the board
    recent_report = generate_report(recent_messages, f"Since {cutoff_date.strftime('%B %d, %Y')}", like_cutoff=2, message_cutoff=100)
    
    # Combine and save
    full_output = complete_report + ["\n"] + recent_report

    with open("chat_analysis_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(full_output))
    
    print("Success! Multi-scale analysis complete. Report saved to 'chat_analysis_report.txt'")

except FileNotFoundError:
    print("Error: The file 'combined_messages.json' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")