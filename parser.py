
import re
import json
import requests

def parse_awesome_list(markdown_content):
    lines = markdown_content.split('\n')

    # Regular expressions for parsing
    main_header_re = re.compile(r'^##\s+(.+)')
    # Level 2 item: e.g., "- [Title](...)"
    list_item_re = re.compile(r'^-+\s+\[([^\]]+)\]\(([^)]+)\)(?:\s+-\s+(.*))?')
    # Level 3 item: e.g., "    - [Title](...)"
    nested_list_item_re = re.compile(r'^\t-\s+\[([^\]]+)\]\(([^)]+)\)(?:\s+-\s+(.*))?')

    category_structure = []
    temp_category_map = {}

    # Pass 1: Extract Level 1 categories from the "Contents" section to establish structure and order.
    in_contents_section = False
    contents_list_item_re = re.compile(r'^-+\s+\[([^\]]+)\]\(([^)]+)\)')
    for line in lines:
        stripped_line = line.strip()
        if stripped_line == '## Contents':
            in_contents_section = True
            continue
        # Any other "##" header marks the end of the Contents section
        if stripped_line.startswith('## '):
            in_contents_section = False

        if in_contents_section:
            match = contents_list_item_re.match(stripped_line)
            if match:
                title = match.group(1).strip()
                link = match.group(2).strip()
                category_info = {
                    "title": title,
                    "link": link,
                    "description": "",
                    "sub_categories": []
                }
                category_structure.append(category_info)
                temp_category_map[title] = category_info

    # Pass 2: Populate Level 2 and Level 3 categories with correct hierarchy.
    current_level1_category = None
    last_level2_category = None

    for line in lines:
        # Don't process empty lines
        if not line.strip():
            continue

        main_header_match = main_header_re.match(line.strip())
        if main_header_match:
            header_title = main_header_match.group(1).strip()
            if header_title in temp_category_map:
                current_level1_category = temp_category_map[header_title]
                # Reset the Level 2 context when a new Level 1 section begins
                last_level2_category = None
            else:
                current_level1_category = None
            continue

        if current_level1_category:
            # Must check for a nested (Level 3) item first because its pattern is more specific.
            # We match against the original `line` to preserve indentation for the regex.
            nested_match = nested_list_item_re.match(line)
            if nested_match and last_level2_category:
                # This is a Level 3 item.
                title = nested_match.group(1).strip()
                link = nested_match.group(2).strip()
                description = nested_match.group(3).strip() if nested_match.group(3) else ""

                # Get the parent (Level 2) title for the prefix.
                parent_title = last_level2_category['title']
                prefixed_title = f"{parent_title} - {title}"

                # Ensure the parent Level 2 item has a 'sub_categories' list.
                if 'sub_categories' not in last_level2_category:
                    last_level2_category['sub_categories'] = []

                # Append the Level 3 item into its parent's 'sub_categories'.
                # last_level2_category['sub_categories'].append({
                #     "title": prefixed_title,
                #     "link": link,
                #     "description": description
                # })

                # For max 2 levels, we can directly append to the current Level 1 category.
                current_level1_category['sub_categories'].append({
                    "title": prefixed_title,
                    "link": link,
                    "description": description
                })
            else:
                # If it's not a nested item, check if it's a regular (Level 2) item.
                list_match = list_item_re.match(line.strip())
                if list_match:
                    # This is a Level 2 item.
                    title = list_match.group(1).strip()
                    link = list_match.group(2).strip()
                    description = list_match.group(3).strip() if list_match.group(3) else ""

                    level2_item = {
                        "title": title,
                        "link": link,
                        "description": description
                    }
                    # Append the new Level 2 item to the current Level 1 category.
                    current_level1_category['sub_categories'].append(level2_item)
                    # Set this item as the context for any subsequent Level 3 items.
                    last_level2_category = level2_item

    return category_structure

if __name__ == "__main__":
    url = "https://raw.githubusercontent.com/sindresorhus/awesome/main/readme.md"
    try:
        print("Fetching awesome/readme.md...")
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        print("Fetch successful.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the remote readme.md: {e}")
        exit(1)

    print("Parsing content...")
    parsed_data = parse_awesome_list(content)
    print("Parsing complete.")

    output_path = "resources/awesome_contents.json"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        print(f"Parsed data successfully saved to {output_path}")
    except IOError as e:
        print(f"Error writing to file {output_path}: {e}")
        exit(1)