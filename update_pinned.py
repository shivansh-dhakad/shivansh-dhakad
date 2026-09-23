import os
import re
import sys

import requests

USERNAME = "shivansh-dhakad"
TOKEN = os.environ.get("GH_TOKEN")

# Hand-written descriptions take priority over the repo's GitHub description.
OVERRIDES = {
    "mobile-price-prediction": "Predicts mobile phone price range from specs",
    "CardioShield-AI": "Cardiovascular risk prediction system",
    "Lumina": "Fully local, private AI-powered study assistant — chat with any document or URL, no cloud, no API keys",
}

ICONS = {
    "mobile-price-prediction": "📱",
    "CardioShield-AI": "🫀",
    "Lumina": "📚",
}
DEFAULT_ICON = "📦"

QUERY = """
query($login: String!) {
  user(login: $login) {
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes {
        ... on Repository {
          name
          url
          description
          primaryLanguage { name }
        }
      }
    }
  }
}
"""


def fetch_pinned():
    if not TOKEN:
        sys.exit("GH_TOKEN is not set")
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": USERNAME}},
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]["pinnedItems"]["nodes"]


def build_table(repos):
    lines = [
        "| Project | What it does | Stack |",
        "|---|---|---|",
    ]
    for r in repos:
        name = r["name"]
        icon = ICONS.get(name, DEFAULT_ICON)
        desc = OVERRIDES.get(name) or r.get("description") or "—"
        desc = desc.replace("|", "\\|")
        lang = r["primaryLanguage"]["name"] if r.get("primaryLanguage") else "—"
        lines.append(f"| {icon} [{name}]({r['url']}) | {desc} | `{lang}` |")
    return "\n".join(lines)


def update_readme(table):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(<!-- PINNED:START -->)(.*?)(<!-- PINNED:END -->)"
    new_content, count = re.subn(
        pattern,
        lambda m: f"{m.group(1)}\n{table}\n{m.group(3)}",
        content,
        flags=re.DOTALL,
    )

    if count == 0:
        sys.exit("PINNED markers not found in README.md")

    if new_content != content:
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("README.md updated")
    else:
        print("No changes")


if __name__ == "__main__":
    repos = fetch_pinned()
    if not repos:
        print("No pinned repos returned (token may lack access). Leaving README unchanged.")
        sys.exit(0)
    update_readme(build_table(repos))
