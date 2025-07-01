import subprocess

AWESOME_LISTS = [
    {
        "url": "https://github.com/sindresorhus/awesome",
        "start_string": "## Platforms"
    },
    {
        "url": "https://github.com/sindresorhus/awesome-nodejs",
        "start_string": "### Mad science"
    },
]

def main():
    for item in AWESOME_LISTS:
        command = [
            "python",
            "parser-awesome.py",
            item["url"],
            item["start_string"]
        ]
        print(f"Running: {' '.join(command)}")
        subprocess.run(command, check=True)
        print("-" * 20)

if __name__ == "__main__":
    main()