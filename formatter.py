import re

# (This script is the same as the last version and will work with the new parser output)
input_filename = "chat_analysis_report.txt" 
output_filename = "chat_summary.md"
try:
    with open(input_filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    time_period, top_giver_stat = "", ""
    leaderboard, giver_leaderboard, most_reacted, top_messages_flat_list = [], [], {}, []
    current_section = None
    for line in lines:
        line = line.strip()
        if not line: continue
        if "Chat History Time Period" in line: current_section = "period"
        elif "Reaction Leaderboard" in line: current_section = "leaderboard"
        elif "Top Reaction Giver" in line: current_section = "top_giver_stat"
        elif "Reaction Giver Leaderboard" in line: current_section = "giver_leaderboard"
        elif "Most Reacted Message" in line: current_section = "most_reacted"
        elif "Messages with More Than 3 Reactions" in line: current_section = "top_messages"
        
        if current_section == "period" and "Messages from:" in line:
            time_period = line
        elif current_section == "leaderboard":
            match = re.match(r"(\d+)\. (.+?): (\d+) Likes \| ([\d\.]+) LPM \| ([\d\.]+) Adjusted LPM", line)
            if match:
                leaderboard.append({"rank": match.group(1), "name": match.group(2), "likes": int(match.group(3)), "lpm": float(match.group(4)), "adj_lpm": float(match.group(5))})
        elif current_section == "top_giver_stat":
            if "gave out the most" in line: top_giver_stat = line
        elif current_section == "giver_leaderboard":
            match = re.match(r"(\d+)\. (.+?): (\d+) reactions given", line)
            if match:
                giver_leaderboard.append({"rank": match.group(1), "name": match.group(2), "count": int(match.group(3))})
        elif current_section == "most_reacted":
            if "Sender:" in line: most_reacted["sender"] = line.split(":", 1)[1].strip()
            elif "Message:" in line: most_reacted["message"] = line.split(":", 1)[1].strip()
            elif "Number of Reactions:" in line: most_reacted["reactions"] = line.split(":", 1)[1].strip()
        elif current_section == "top_messages":
            match = re.match(r"(.+?): (.+) \| Reactions: (\d+)", line)
            if match:
                top_messages_flat_list.append({"sender": match.group(1), "message": match.group(2), "reactions": int(match.group(3))})

    grouped_top_messages = {}
    for msg in top_messages_flat_list:
        sender = msg["sender"]
        if sender not in grouped_top_messages: grouped_top_messages[sender] = []
        grouped_top_messages[sender].append({"message": msg["message"], "reactions": msg["reactions"]})
    for sender in grouped_top_messages:
        grouped_top_messages[sender].sort(key=lambda x: x['reactions'], reverse=True)

    with open(output_filename, "w", encoding="utf-8") as md_file:
        md_file.write("# Chat Summary\n")
        md_file.write(f"_{time_period}_\n\n")
        if most_reacted:
            md_file.write("## 🏆 Most Reacted Message\n")
            md_file.write(f"> **{most_reacted.get('sender')}** with **{most_reacted.get('reactions')}** reactions:\n")
            md_file.write(f"> {most_reacted.get('message')}\n\n")
        if leaderboard:
            md_file.write("## 📈 Reaction Leaderboard\n")
            md_file.write("| Rank | Sender | Total Likes | Likes/Message | Adjusted LPM |\n")
            md_file.write("|:----:|:-------|:-----------:|:-------------:|:------------:|\n")
            for item in leaderboard:
                md_file.write(f"| {item['rank']} | {item['name']} | {item['likes']} | {item['lpm']:.2f} | **{item['adj_lpm']:.2f}** |\n")
            md_file.write("\n")
        if top_giver_stat:
            md_file.write(f"## 🥇 Top Reaction Giver\n**{top_giver_stat}**\n\n")
        if giver_leaderboard:
            md_file.write("## 🙌 Reaction Giver Leaderboard\n")
            md_file.write("| Rank | Sender | Reactions Given |\n")
            md_file.write("|:----:|:-------|:---------------:|\n")
            for item in giver_leaderboard:
                md_file.write(f"| {item['rank']} | {item['name']} | {item['count']} |\n")
            md_file.write("\n")
        if grouped_top_messages:
            md_file.write("## ⭐ Hall of Fame (Messages with > 3 Reactions)\n")
            sorted_senders = sorted(grouped_top_messages.keys(), key=lambda s: len(grouped_top_messages[s]), reverse=True)
            for sender in sorted_senders:
                user_messages = grouped_top_messages[sender]
                md_file.write(f"\n### {sender} ({len(user_messages)} messages)\n")
                md_file.write("| Reactions | Message |\n"); md_file.write("|:---------:|:--------|\n")
                for item in user_messages:
                    md_file.write(f"| {item['reactions']} | {item['message'].replace('|', '\|')} |\n")

    print(f"Success! The full report has been formatted into '{output_filename}'.")
except FileNotFoundError:
    print(f"Error: The input file '{input_filename}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")