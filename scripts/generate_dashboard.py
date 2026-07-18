#!/usr/bin/env python3
import json
import os
import sys
import datetime
import html

HERE = os.path.dirname(os.path.abspath(__file__))
MERGED_PATH = os.path.join(HERE, "../merged_prs_filtered.json")
ACTIVE_PATH = os.path.join(HERE, "../active_prs_filtered.json")
OPEN_ISSUES_PATH = os.path.join(HERE, "../open_issues_filtered.json")
CLOSED_ISSUES_PATH = os.path.join(HERE, "../closed_issues_filtered.json")
MD_OUT_PATH = os.path.join(HERE, "../dashboard.md")
SVG_OUT_PATH = os.path.join(HERE, "../oss-dashboard.svg")

# Terminal styling constants
W = 860
PAD = 20
TITLEBAR_H = 30
KEY_X = PAD
VAL_X = PAD + 140
LINE_H = 20.5

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
KEY = "#ffa657"      # orange keys
SECTION = "#58a6ff"  # blue section headers
GREEN = "#3fb950"
ACCENT = "#22d3ee"

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

def get_repo_full_name(item):
    url = item.get("repository_url", "")
    parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return "unknown"

def esc(s):
    return html.escape(s)

def clean_title(title, max_len=68):
    if len(title) > max_len:
        return title[:max_len-3] + "..."
    return title

def build_svg_rows(merged_total, sorted_orgs, active_items, open_items, closed_items):
    orgs_str_list = [f"{org} ({count})" for org, count in sorted_orgs]
    orgs_details = ", ".join(orgs_str_list) if orgs_str_list else "None"

    rows = [
        ("host",),
        ("sec", "Contributions Summary"),
        ("kv", "Merged PRs", f"{merged_total} total across {len(sorted_orgs)} orgs ({orgs_details})"),
    ]

    # Active PRs
    active_str = f"{len(active_items)} active pull requests"
    rows.append(("kv", "Active PRs", active_str))

    # Issues
    issues_str = f"{len(open_items)} open, {len(closed_items)} closed"
    rows.append(("kv", "Issues Summary", issues_str))

    # Add active PR lists if they exist
    if active_items:
        rows.append(("gap",))
        rows.append(("sec", "Active Pull Requests"))
        for item in active_items[:3]:
            title = clean_title(item.get("title", "Untitled PR"))
            repo = get_repo_full_name(item)
            rows.append(("bul", f"{title} (in {repo})"))

    # Add open issues if they exist
    if open_items:
        rows.append(("gap",))
        rows.append(("sec", "Open Issues"))
        for item in open_items[:2]:
            title = clean_title(item.get("title", "Untitled Issue"))
            repo = get_repo_full_name(item)
            rows.append(("bul", f"{title} (in {repo})"))

    return rows

def generate_svg(rows):
    # Calculate height dynamically based on rows
    h_content = TITLEBAR_H + 30
    for r in rows:
        if r[0] == "gap":
            h_content += LINE_H * 0.5
        else:
            h_content += LINE_H
    H = int(h_content + 15)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs>',
        f'<linearGradient id="dbbg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>',
        '</linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#dbbg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    
    parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
                 f'text-anchor="middle">utkarsh@github: ~$ ./oss-dashboard.sh</text>')

    y = TITLEBAR_H + 30
    for row in rows:
        kind = row[0]
        if kind == "gap":
            y += LINE_H * 0.5
            continue
        
        if kind == "host":
            inner = (f'<text x="{KEY_X}" y="{y:.1f}" font-size="14" font-weight="700">'
                     f'<tspan fill="{GREEN}">utkarsh</tspan><tspan fill="{MUTED}">@</tspan>'
                     f'<tspan fill="{ACCENT}">github</tspan></text>'
                     f'<line x1="{KEY_X+116}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
                     f'stroke="{FRAME}" stroke-opacity="0.8"/>')
        elif kind == "sec":
            title = esc(row[1])
            inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{SECTION}" font-size="12.5" font-weight="700">'
                     f'&#8212; {title}</text>'
                     f'<line x1="{KEY_X + 12 + len(row[1])*8}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
                     f'stroke="{FRAME}" stroke-opacity="0.8"/>')
        elif kind == "kv":
            key, val = esc(row[1]), esc(row[2])
            inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{KEY}" font-size="12.5" font-weight="700">{key}</text>'
                     f'<text x="{VAL_X}" y="{y:.1f}" fill="{INK}" font-size="12.5">{val}</text>')
        elif kind == "bul":
            txt = esc(row[1])
            inner = (f'<circle cx="{KEY_X+5}" cy="{y-4:.1f}" r="2.5" fill="{GREEN}"/>'
                     f'<text x="{KEY_X+16}" y="{y:.1f}" fill="{INK}" font-size="12.5">{txt}</text>')
        else:
            continue
        
        parts.append(f'<g>{inner}</g>')
        y += LINE_H

    parts.append("</svg>")
    return "".join(parts)

def generate_markdown(sorted_orgs):
    lines = []
    lines.append('<div align="center">')
    lines.append('  <img src="./oss-dashboard.svg" width="860" alt="Open Source Dashboard" />')
    lines.append('</div>')
    lines.append("")
    lines.append('<br/>')
    lines.append("")
    
    if sorted_orgs:
        lines.append('<div align="center">')
        for org, count in sorted_orgs:
            lines.append(f'  <a href="https://github.com/{org}" title="{org}: {count} PR(s)"><img src="https://github.com/{org}.png?size=32" width="32" height="32" style="border-radius:6px;margin:2px" alt="{org}"/></a>')
        lines.append('</div>')
        lines.append("")
        
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %H:%M:%S UTC %Y")
    lines.append(f'<div align="center">')
    lines.append(f'  <i>Last updated: {now_utc}</i>')
    lines.append(f'</div>')
    
    return "\n".join(lines) + "\n"

def main():
    merged_data = load_json(MERGED_PATH)
    active_data = load_json(ACTIVE_PATH)
    open_issues_data = load_json(OPEN_ISSUES_PATH)
    closed_issues_data = load_json(CLOSED_ISSUES_PATH)

    merged_items = merged_data.get("items", [])
    active_items = active_data.get("items", [])
    open_items = open_issues_data.get("items", [])
    closed_items = closed_issues_data.get("items", [])

    # Compute org stats for merged PRs
    org_counts = {}
    for item in merged_items:
        org = get_repo_org(item)
        org_counts[org] = org_counts.get(org, 0) + 1

    sorted_orgs = sorted(org_counts.items(), key=lambda x: x[1], reverse=True)

    # Build SVG rows & generate SVG
    rows = build_svg_rows(len(merged_items), sorted_orgs, active_items, open_items, closed_items)
    svg_content = generate_svg(rows)
    
    with open(SVG_OUT_PATH, "w") as f:
        f.write(svg_content)
        
    # Generate Markdown wrapper
    md_content = generate_markdown(sorted_orgs)
    with open(MD_OUT_PATH, "w") as f:
        f.write(md_content)

    print(f"Generated {SVG_OUT_PATH} and {MD_OUT_PATH} successfully.")

if __name__ == "__main__":
    main()
