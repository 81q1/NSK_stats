import os
import shutil
import re

# --- Configuration ---
input_md = "chat_summary.md"
export_dir = "github_export"
media_dir = os.path.join(export_dir, "media")
output_md = os.path.join(export_dir, "index.md")

def main():
    if not os.path.exists(input_md):
        print(f"Error: Could not find '{input_md}'.")
        return

    # Create the base media directory
    os.makedirs(media_dir, exist_ok=True)
    print(f"Created export directory: {export_dir}/")

    with open(input_md, "r", encoding="utf-8") as file:
        content = file.read()

    # Find paths in all formats: [Photo: path], [Video: path], or src="path"
    raw_photos = re.findall(r'\[Photo: (.*?)\]', content)
    raw_videos = re.findall(r'\[Video: (.*?)\]', content)
    html_srcs = re.findall(r'src="(.*?)"', content)
    
    # Combine them all into a unique set so we don't copy duplicates
    unique_paths = set(raw_photos + raw_videos + html_srcs)
    
    copied_count = 0
    missing_count = 0

    print(f"Found {len(unique_paths)} unique media files referenced in the Markdown.")

    for old_path in unique_paths:
        # Skip external web links
        if old_path.startswith("http://") or old_path.startswith("https://"):
            continue
            
        # --- THE FIX: Extract only the last two sections ---
        # Split the path by forward slash (standard for Instagram JSON/HTML exports)
        path_parts = old_path.replace('\\', '/').split('/')
        
        if len(path_parts) >= 2:
            # Grab just the folder name (e.g., 'photos') and file name (e.g., 'image.jpg')
            subfolder = path_parts[-2]
            filename = path_parts[-1]
            local_source_path = os.path.join(subfolder, filename)
        else:
            subfolder = "other"
            filename = old_path
            local_source_path = old_path

        # Verify the local file actually exists using the shortened path
        if os.path.exists(local_source_path):
            
            # Ensure the specific subfolder exists inside our export directory
            os.makedirs(os.path.join(media_dir, subfolder), exist_ok=True)
            
            new_relative_path = f"media/{subfolder}/{filename}"
            new_absolute_path = os.path.join(export_dir, new_relative_path)
            
            # Handle files with the exact same name
            counter = 1
            while os.path.exists(new_absolute_path):
                name, ext = os.path.splitext(filename)
                new_relative_path = f"media/{subfolder}/{name}_{counter}{ext}"
                new_absolute_path = os.path.join(export_dir, new_relative_path)
                counter += 1
            
            # Copy the file using the SHORTENED local path
            shutil.copy2(local_source_path, new_absolute_path)
            copied_count += 1
            
            # --- UPDATE THE MARKDOWN ---
            # We still replace the LONG path in the markdown text so it matches up properly
            content = content.replace(f"[Photo: {old_path}]", f'<br><img src="{new_relative_path}" height="150">')
            content = content.replace(f"[Video: {old_path}]", f'<br><video src="{new_relative_path}" height="150" controls></video>')
            content = content.replace(old_path, new_relative_path)
            
        else:
            print(f"Warning: Could not find source file -> {local_source_path} (extracted from {old_path})")
            missing_count += 1

    # Clean up GIFs and Shared Links into clickable links
    content = re.sub(r'\[GIF: (.*?)\]', r'[🔗 View GIF](\1)', content)
    content = re.sub(r'\[Shared Link: (.*?)\]', r'[🔗 Shared Link](\1)', content)

    # Write the beautifully formatted, updated Markdown as index.md
    with open(output_md, "w", encoding="utf-8") as file:
        file.write(content)

    print("\n--- Export Complete ---")
    print(f"Successfully copied: {copied_count} files.")
    if missing_count > 0:
        print(f"Failed to find: {missing_count} files (Check warnings above).")
    print(f"\nYour site is ready! Run your git commands inside the '{export_dir}' folder.")

if __name__ == "__main__":
    main()