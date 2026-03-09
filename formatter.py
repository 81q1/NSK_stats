import re

input_filename = "chat_analysis_report.txt" 
output_filename = "chat_summary.md"

def format_media_for_markdown(text):
    # Escape pipe characters so they don't break Markdown tables
    text = text.replace('|', '\\|')
    
    # Convert [Photo: path] to an HTML image tag (height constrained for tables)
    text = re.sub(r'\[Photo: (.*?)\]', r'<br><img src="\1" height="150">', text)
    
    # Convert [Video: path] to an HTML video tag
    text = re.sub(r'\[Video: (.*?)\]', r'<br><video src="\1" height="150" controls></video>', text)
    
    # Convert GIFs and Shared Links into clickable Markdown links
    text = re.sub(r'\[GIF: (.*?)\]', r'[🔗 View GIF](\1)', text)
    text = re.sub(r'\[Shared Link: (.*?)\]', r'[🔗 Shared Link](\1)', text)
    
    return text

try:
    with open(input_filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    reports = []
    current_report = None
    current_section = None

    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Detect new time-scale section
        if line.startswith("=== SECTION:"):
            if current_report:
                reports.append(current_report)
            current_report = {
                "title": line.split("=== SECTION:")[1].strip(" ="),
                "time_period": "",
                "top_giver_stat": "",
                "leaderboard": [],
                "giver_leaderboard": [],
                "most_reacted": {},
                "top_messages_flat_list": []
            }
            current_section = None
            continue
            
        if not current_report:
            continue

        if "Chat History Time Period" in line: current_section = "period"
        elif "Reaction Leaderboard" in line: current_section = "leaderboard"
        elif "Top Reaction Giver" in line: current_section = "top_giver_stat"
        elif "Reaction Giver Leaderboard" in line: current_section = "giver_leaderboard"
        elif "Most Reacted Message" in line: current_section = "most_reacted"
        elif "Messages with More Than 3 Reactions" in line: current_section = "top_messages"
        
        if current_section == "period" and "Messages from:" in line:
            current_report["time_period"] = line
        elif current_section == "leaderboard":
            match = re.match(r"(\d+)\. (.+?): (\d+) Likes \| ([\d\.]+) LPM \| ([\d\.]+) Adjusted LPM", line)
            if match:
                current_report["leaderboard"].append({"rank": match.group(1), "name": match.group(2), "likes": int(match.group(3)), "lpm": float(match.group(4)), "adj_lpm": float(match.group(5))})
        elif current_section == "top_giver_stat":
            if "gave out the most" in line: current_report["top_giver_stat"] = line
        elif current_section == "giver_leaderboard":
            match = re.match(r"(\d+)\. (.+?): (\d+) reactions given", line)
            if match:
                current_report["giver_leaderboard"].append({"rank": match.group(1), "name": match.group(2), "count": int(match.group(3))})
        elif current_section == "most_reacted":
            if "Sender:" in line: current_report["most_reacted"]["sender"] = line.split(":", 1)[1].strip()
            elif "Message:" in line: current_report["most_reacted"]["message"] = line.split(":", 1)[1].strip()
            elif "Number of Reactions:" in line: current_report["most_reacted"]["reactions"] = line.split(":", 1)[1].strip()
        elif current_section == "top_messages":
            match = re.match(r"(.+?): (.+) \| Reactions: (\d+)", line)
            if match:
                current_report["top_messages_flat_list"].append({"sender": match.group(1), "message": match.group(2), "reactions": int(match.group(3))})

    # Append the last report block
    if current_report:
        reports.append(current_report)

    with open(output_filename, "w", encoding="utf-8") as md_file:
        md_file.write("# Chat Summary\n\n")
        
        for report in reports:
            md_file.write(f"---\n\n# 📅 {report['title']}\n")
            md_file.write(f"_{report['time_period']}_\n\n")
            
            most_reacted = report["most_reacted"]
            if most_reacted and most_reacted.get("sender"):
                md_file.write("## 🏆 Most Reacted Message\n")
                md_file.write(f"> **{most_reacted.get('sender')}** with **{most_reacted.get('reactions')}** reactions:\n")
                
                # Format the Most Reacted Message
                formatted_msg = format_media_for_markdown(most_reacted.get('message', ''))
                md_file.write(f"> {formatted_msg}\n\n")
            
            if report["leaderboard"]:
                md_file.write("## 📈 Reaction Leaderboard\n")
                md_file.write("| Rank | Sender | Total Likes | Likes/Message | Adjusted LPM |\n")
                md_file.write("|:----:|:-------|:-----------:|:-------------:|:------------:|\n")
                for item in report["leaderboard"]:
                    md_file.write(f"| {item['rank']} | {item['name']} | {item['likes']} | {item['lpm']:.2f} | **{item['adj_lpm']:.2f}** |\n")
                md_file.write("\n")
            
            if report["top_giver_stat"]:
                md_file.write(f"## 🥇 Top Reaction Giver\n**{report['top_giver_stat']}**\n\n")
            
            if report["giver_leaderboard"]:
                md_file.write("## 🙌 Reaction Giver Leaderboard\n")
                md_file.write("| Rank | Sender | Reactions Given |\n")
                md_file.write("|:----:|:-------|:---------------:|\n")
                for item in report["giver_leaderboard"]:
                    md_file.write(f"| {item['rank']} | {item['name']} | {item['count']} |\n")
                md_file.write("\n")
            
            grouped_top_messages = {}
            for msg in report["top_messages_flat_list"]:
                sender = msg["sender"]
                if sender not in grouped_top_messages: grouped_top_messages[sender] = []
                grouped_top_messages[sender].append({"message": msg["message"], "reactions": msg["reactions"]})
            
            for sender in grouped_top_messages:
                grouped_top_messages[sender].sort(key=lambda x: x['reactions'], reverse=True)

            if grouped_top_messages:
                md_file.write("## ⭐ Hall of Fame (Messages with > 3 Reactions)\n")
                sorted_senders = sorted(grouped_top_messages.keys(), key=lambda s: len(grouped_top_messages[s]), reverse=True)
                for sender in sorted_senders:
                    user_messages = grouped_top_messages[sender]
                    md_file.write(f"\n### {sender} ({len(user_messages)} messages)\n")
                    md_file.write("| Reactions | Message |\n"); md_file.write("|:---------:|:--------|\n")
                    for item in user_messages:
                        # Format the Hall of Fame messages
                        formatted_item_msg = format_media_for_markdown(item['message'])
                        md_file.write(f"| {item['reactions']} | {formatted_item_msg} |\n")
            
            md_file.write("\n<br>\n\n")

    print(f"Success! The full multi-scale report (with inline media) has been formatted into '{output_filename}'.")
except FileNotFoundError:
    print(f"Error: The input file '{input_filename}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")