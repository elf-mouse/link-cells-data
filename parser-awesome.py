import re
import json
import requests
import sys

def parse_awesome_list(markdown_content, start_string):
    lines = markdown_content.split('\n')

    # Dynamically determine the header level from the start_string
    header_match = re.match(r'^(#+)\s', start_string.strip())
    if not header_match:
        print(f"Error: start_string '{start_string}' is not a valid markdown header (e.g., '## Platforms').")
        return []

    header_prefix = header_match.group(1)
    main_header_re = re.compile(rf'^{re.escape(header_prefix)}\s+(.+)')

    # Regular expressions for parsing
    list_item_re = re.compile(r'^-+\s+\[([^\]]+)\]\(([^)]+)\)(?:\s+-\s+(.*))?')
    nested_list_item_re = re.compile(r'^\s+-\s+\[([^\]]+)\]\(([^)]+)\)(?:\s+-\s+(.*))?')

    categories = []
    current_category = None
    last_level2_item = None
    parsing_started = False

    for line in lines:
        if not parsing_started:
            if line.strip() == start_string.strip():
                parsing_started = True
            else:
                continue

        main_header_match = main_header_re.match(line.strip())
        if main_header_match:
            category_name = main_header_match.group(1).strip()
            current_category = {
                "name": category_name,
                "sub_categories": []
            }
            categories.append(current_category)
            last_level2_item = None
            continue

        if current_category:
            nested_match = nested_list_item_re.match(line)
            if nested_match:
                name = nested_match.group(1).strip()
                repo = nested_match.group(2).strip()
                brief = nested_match.group(3).strip() if nested_match.group(3) else ""

                if last_level2_item:
                    parent_name = last_level2_item['name']
                    prefixed_name = f"{parent_name} - {name}"

                    current_category['sub_categories'].append({
                        "name": prefixed_name,
                        "repo": repo,
                        "brief": brief,
                    })
            else:
                list_match = list_item_re.match(line.strip())
                if list_match:
                    name = list_match.group(1).strip()
                    repo = list_match.group(2).strip()
                    brief = list_match.group(3).strip() if list_match.group(3) else ""

                    level2_item = {
                        "name": name,
                        "repo": repo,
                        "brief": brief,
                    }
                    current_category['sub_categories'].append(level2_item)
                    last_level2_item = level2_item

    return categories

import os

def process_and_save(url, start_string):
    try:
        print(f"Fetching {url}...")
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        print("Fetch successful.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the remote readme.md: {e}")
        return

    print("Parsing content...")
    parsed_data = parse_awesome_list(content, start_string)
    print("Parsing complete.")

    try:
        repo_name = url.split('/')[4]
    except IndexError:
        print(f"Could not determine repository name from URL: {url}")
        return

    output_dir = "dist"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, f"{repo_name}.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        print(f"Parsed data successfully saved to {output_path}")
    except IOError as e:
        print(f"Error writing to file {output_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python parser-awesome.py <github_repo_url> <parser_start_string>")
        print("Example: python parser-awesome.py https://github.com/sindresorhus/awesome '## Platforms'")
        sys.exit(1)

    repo_url = sys.argv[1]
    start_string = sys.argv[2]

    # Construct the raw URL
    if "github.com" in repo_url:
        parts = repo_url.split('/')
        if len(parts) >= 5:
            user = parts[3]
            repo = parts[4]
            url = f"https://raw.githubusercontent.com/{user}/{repo}/main/readme.md"
        else:
            print("Invalid GitHub repository URL format.")
            sys.exit(1)
    else:
        url = repo_url

    process_and_save(url, start_string)