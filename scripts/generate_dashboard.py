#!/usr/bin/env python3
import json
import os
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
MERGED_PATH = os.path.join(HERE, "../merged_prs_filtered.json")
ACTIVE_PATH = os.path.join(HERE, "../active_prs_filtered.json")
OPEN_ISSUES_PATH = os.path.join(HERE, "../open_issues_filtered.json")
CLOSED_ISSUES_PATH = os.path.join(HERE, "../closed_issues_filtered.json")
OUT_PATH = os.path.join(HERE, "../dashboard.md")

def load_json(path):
    if not os.path.exists(path):
        return {"items": []}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {"items": []}

def get_repo_org(item):
    url = item.get("repository_url", "")
    parts = url.split("/")
    if len(parts) >= 2:
        return parts[-2]
    return "unknown"

def main():
    merged_data = load_json(MERGED_PATH)
    active_data = load_json(ACTIVE_PATH)
    open_issues_data = load_json(OPEN_ISSUES_PATH)
    closed_issues_data = load_json(CLOSED_ISSUES_PATH)

    merged_items = merged_data.get("items", [])
    active_items = active_data.get("items", [])
    open_items = open_issues_data.get("items", [])
    closed_items = closed_issues_data.get("items", [])

    merged_total = len(merged_items)
    active_total = len(active_items)
    open_total = len(open_items)
    closed_total = len(closed_items)

    # Compute org stats for merged PRs
    org_counts = {}
    for item in merged_items:
        org = get_repo_org(item)
        org_counts[org] = org_counts.get(org, 0) + 1

    # Sort orgs by PR count descending
    sorted_orgs = sorted(org_counts.items(), key=lambda x: x[1], reverse=True)
    orgs_str_list = [f"`{org}` ({count})" for org, count in sorted_orgs]
    orgs_details = " • ".join(orgs_str_list) if orgs_str_list else "_No merged PRs_"

    lines = []
    lines.append("### 🚀 Open Source Activity")
    lines.append("")
    lines.append("| Activity | Count | Details |")
    lines.append("| :--- | :---: | :--- |")
    lines.append(f"| **Merged Pull Requests** | **{merged_total}** | {orgs_details} |")
    
    if active_total > 0:
        active_repos = {}
        for item in active_items:
            org = get_repo_org(item)
            active_repos[org] = active_repos.get(org, 0) + 1
        active_details = " • ".join([f"`{org}` ({c})" for org, c in sorted(active_repos.items())])
    else:
        active_details = "_No active pull requests_"
    lines.append(f"| **Active Pull Requests** | **{active_total}** | {active_details} |")

    # Open / Closed Issues
    issues_details = []
    if open_total > 0:
        issues_details.append(f"{open_total} open")
    if closed_total > 0:
        issues_details.append(f"{closed_total} closed")
    issues_str = " • ".join(issues_details) if issues_details else "_No active issues_"
    lines.append(f"| **Issues Summary** | **{open_total + closed_total}** | {issues_str} |")
    lines.append("")

    # Display organization logo badges
    if sorted_orgs:
        lines.append('<div align="left">')
        lines.append("")
        for org, count in sorted_orgs:
            lines.append(f'<a href="https://github.com/{org}" title="{org}: {count} PR(s)"><img src="https://github.com/{org}.png?size=32" width="32" height="32" style="border-radius:6px;margin:2px" alt="{org}"/></a>')
        lines.append("")
        lines.append("</div>")
        lines.append("")

    # If there are active PRs or issues, list them cleanly below in a very minimal way
    if active_items:
        lines.append("#### 🔄 Active Pull Requests")
        for item in active_items:
            title = item.get("title", "Untitled PR")
            url = item.get("html_url", "#")
            repo_url = item.get("repository_url", "")
            repo_parts = repo_url.split("/")
            repo_name = f"{repo_parts[-2]}/{repo_parts[-1]}" if len(repo_parts) >= 2 else "unknown"
            lines.append(f"- [{title}]({url}) in **{repo_name}**")
        lines.append("")

    if open_items:
        lines.append("#### 🐛 Open Issues")
        for item in open_items:
            title = item.get("title", "Untitled Issue")
            url = item.get("html_url", "#")
            repo_url = item.get("repository_url", "")
            repo_parts = repo_url.split("/")
            repo_name = f"{repo_parts[-2]}/{repo_parts[-1]}" if len(repo_parts) >= 2 else "unknown"
            lines.append(f"- [{title}]({url}) in **{repo_name}**")
        lines.append("")

    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %H:%M:%S UTC %Y")
    lines.append(f"_{{Last updated: {now_utc}}}_")
    
    with open(OUT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    main()
