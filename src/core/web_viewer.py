"""Web viewer static site generator for Pasture scraper.

This module generates a static HTML/CSS/JS website for browsing scraped content.
It scans the output directory structure and creates JSON indices along with static assets.
"""

import os
import json
import logging
import re
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

logger = logging.getLogger(__name__)


def generate_static_site(output_base_dir: str) -> None:
    """Generate static web viewer site.

    Args:
        output_base_dir: Base output directory containing scraped content
    """
    logger.info("📊 Generating web viewer...")

    viewer_dir = os.path.join(output_base_dir, "viewer")
    data_dir = os.path.join(viewer_dir, "data")
    assets_dir = os.path.join(viewer_dir, "assets")

    # Create directories
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    # Scan scraped content
    content_data = scan_scraped_content(output_base_dir)

    # Generate JSON indices
    generate_index_json(content_data, data_dir)
    generate_daily_json_files(content_data, data_dir)

    # Create static assets
    create_static_assets(viewer_dir)

    total_articles = sum(day["total_articles"] for day in content_data["dates"])
    logger.info(f"📊 Web viewer generated: {len(content_data['dates'])} days, {total_articles} articles")


def scan_scraped_content(output_base_dir: str) -> Dict[str, Any]:
    """Scan output directory and collect article metadata.

    Args:
        output_base_dir: Base output directory

    Returns:
        Dictionary with dates, sources, and article metadata
    """
    content_data = {
        "generated_at": datetime.now().isoformat() + "Z",
        "dates": [],
        "sources": set(),
        "articles_by_date": {}  # date -> list of articles
    }

    # Walk through directory structure: <source>/<YYYY>/<MM>/<DD>/*.md
    for source_name in os.listdir(output_base_dir):
        source_path = os.path.join(output_base_dir, source_name)

        # Skip non-directories, special directories, and year directories (old structure)
        if (not os.path.isdir(source_path) or
            source_name in ["viewer", "processed_urls.json", "logs"] or
            (source_name.isdigit() and len(source_name) == 4)):  # Skip year directories like "2025"
            continue

        content_data["sources"].add(source_name)

        # Walk through year/month/day structure
        for root, dirs, files in os.walk(source_path):
            # Only process directories that contain .md files
            md_files = [f for f in files if f.endswith(".md")]
            if not md_files:
                continue

            # Extract date from path: source/YYYY/MM/DD
            path_parts = Path(root).parts
            try:
                # Find the source name in path and get date parts after it
                source_idx = path_parts.index(source_name)
                if len(path_parts) >= source_idx + 4:
                    year = path_parts[source_idx + 1]
                    month = path_parts[source_idx + 2]
                    day = path_parts[source_idx + 3]
                    date_str = f"{year}-{month}-{day}"
                else:
                    continue
            except (ValueError, IndexError):
                continue

            # Initialize date entry if needed
            if date_str not in content_data["articles_by_date"]:
                content_data["articles_by_date"][date_str] = []

            # Process each markdown file
            for md_file in md_files:
                file_path = os.path.join(root, md_file)
                try:
                    metadata = extract_article_metadata(file_path, source_name, date_str, output_base_dir)
                    content_data["articles_by_date"][date_str].append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to extract metadata from {file_path}: {e}")

    # Convert articles_by_date to dates list with counts
    dates_list = []
    for date_str in sorted(content_data["articles_by_date"].keys(), reverse=True):
        articles = content_data["articles_by_date"][date_str]

        # Count by source
        sources_count = {}
        for article in articles:
            source = article["source"]
            sources_count[source] = sources_count.get(source, 0) + 1

        dates_list.append({
            "date": date_str,
            "sources": sources_count,
            "total_articles": len(articles)
        })

    content_data["dates"] = dates_list
    content_data["sources"] = sorted(list(content_data["sources"]))

    return content_data


def extract_article_metadata(file_path: str, source: str, date_str: str, base_dir: str) -> Dict[str, Any]:
    """Extract metadata from a markdown file.

    Args:
        file_path: Path to markdown file
        source: Source name (e.g., 'worldnews')
        date_str: Date string (YYYY-MM-DD)
        base_dir: Base output directory for relative path calculation

    Returns:
        Dictionary with article metadata
    """
    file_name = os.path.basename(file_path)
    file_id = file_name.replace(".md", "")

    # Read file content (first 1000 chars for title and preview)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(1000)
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        content = ""

    title = get_article_title(content)
    preview = get_article_preview(content)

    # Calculate relative path from viewer/ to the markdown file
    # viewer/ -> ../<source>/<YYYY>/<MM>/<DD>/<file>.md
    rel_path = os.path.relpath(file_path, os.path.join(base_dir, "viewer"))

    # Get file modification time as scraped_at
    try:
        mtime = os.path.getmtime(file_path)
        scraped_at = datetime.fromtimestamp(mtime).isoformat() + "Z"
    except:
        scraped_at = date_str + "T00:00:00Z"

    return {
        "id": file_id,
        "title": title,
        "source": source,
        "file_path": rel_path,
        "scraped_at": scraped_at,
        "preview": preview
    }


def get_article_title(content: str) -> str:
    """Extract title from markdown content.

    Tries to find first H1 heading, otherwise uses first line.

    Args:
        content: Markdown content

    Returns:
        Extracted title (max 100 chars)
    """
    if not content:
        return "Untitled"

    lines = content.strip().split("\n")

    # Try to find H1 heading
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            return title[:100] if len(title) > 100 else title

    # Use first non-empty line
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            # Remove markdown formatting
            line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)  # Remove links
            line = re.sub(r"[*_`]", "", line)  # Remove emphasis
            return line[:100] if len(line) > 100 else line

    return "Untitled"


def get_article_preview(content: str, max_length: int = 200) -> str:
    """Extract preview text from markdown content.

    Args:
        content: Markdown content
        max_length: Maximum preview length

    Returns:
        Preview text
    """
    if not content:
        return ""

    lines = content.strip().split("\n")

    # Skip title and empty lines
    text_lines = []
    skip_first_heading = False

    for line in lines:
        line = line.strip()

        # Skip first H1
        if line.startswith("# ") and not skip_first_heading:
            skip_first_heading = True
            continue

        # Skip empty lines and other headings
        if not line or line.startswith("#"):
            continue

        text_lines.append(line)

        # Stop when we have enough text
        if len(" ".join(text_lines)) > max_length:
            break

    preview = " ".join(text_lines)

    # Remove markdown formatting
    preview = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", preview)  # Remove links
    preview = re.sub(r"[*_`]", "", preview)  # Remove emphasis

    # Truncate and add ellipsis
    if len(preview) > max_length:
        preview = preview[:max_length].rsplit(" ", 1)[0] + "..."

    return preview


def generate_index_json(content_data: Dict[str, Any], data_dir: str) -> None:
    """Generate main index.json file.

    Args:
        content_data: Content data dictionary
        data_dir: Data directory path
    """
    index_data = {
        "generated_at": content_data["generated_at"],
        "dates": content_data["dates"],
        "sources": content_data["sources"]
    }

    index_path = os.path.join(data_dir, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2)


def generate_daily_json_files(content_data: Dict[str, Any], data_dir: str) -> None:
    """Generate per-day JSON files.

    Args:
        content_data: Content data dictionary
        data_dir: Data directory path
    """
    for date_str, articles in content_data["articles_by_date"].items():
        daily_data = {
            "date": date_str,
            "articles": sorted(articles, key=lambda x: x["scraped_at"], reverse=True)
        }

        daily_path = os.path.join(data_dir, f"{date_str}.json")
        with open(daily_path, "w", encoding="utf-8") as f:
            json.dump(daily_data, f, indent=2)


def create_static_assets(viewer_dir: str) -> None:
    """Create static HTML/CSS/JS files.

    Args:
        viewer_dir: Viewer directory path
    """
    create_index_html(viewer_dir)
    create_stylesheet(os.path.join(viewer_dir, "assets"))
    create_javascript(os.path.join(viewer_dir, "assets"))


def create_index_html(viewer_dir: str) -> None:
    """Create index.html file.

    Args:
        viewer_dir: Viewer directory path
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐄 Pasture</title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🐄 Pasture</h1>
            <div class="header-controls">
                <button id="calendar-toggle" aria-label="Toggle calendar">📅</button>
                <button id="settings-toggle" aria-label="Toggle settings">⚙️</button>
                <button id="theme-toggle" aria-label="Toggle theme">◐</button>
            </div>
        </header>

        <div id="calendar-overlay" class="calendar-overlay">
            <div class="calendar-container">
                <div class="calendar-header">
                    <button id="prev-month">&lt;</button>
                    <h2 id="current-month"></h2>
                    <button id="next-month">&gt;</button>
                </div>
                <div id="calendar"></div>
            </div>
        </div>

        <div id="settings-overlay" class="settings-overlay">
            <div class="settings-container">
                <div class="settings-header">
                    <h2>Settings</h2>
                    <button id="settings-close" aria-label="Close settings">✕</button>
                </div>
                <div class="settings-content">
                    <h3>Configuration (config.ini)</h3>
                    <textarea id="config-content" class="config-editor" spellcheck="false">Loading...</textarea>
                    <div class="settings-actions">
                        <button id="save-config" class="save-button">Save Changes</button>
                        <span id="save-status" class="save-status"></span>
                    </div>
                </div>
            </div>
        </div>

        <div class="source-filters">
            <button class="filter-btn active" data-source="all">All</button>
        </div>

        <div class="main-content">
            <aside class="timeline">
                <div id="article-list"></div>
            </aside>

            <main class="viewer">
                <div id="article-content">
                    <div class="welcome">
                        <h2>Welcome to 🐄 Pasture</h2>
                        <p>Select a date from the calendar to browse scraped articles.</p>
                    </div>
                </div>
            </main>
        </div>

        <div class="stats-section">
            <h3>Statistics</h3>
            <div id="stats-content">
                <p class="stats-placeholder">Select a date to view statistics</p>
            </div>
            <div id="stats-charts" class="stats-charts-hidden">
                <div class="chart-container">
                    <h4>Source Distribution</h4>
                    <canvas id="source-radar-chart"></canvas>
                </div>
                <div class="chart-container">
                    <h4>Article Metrics</h4>
                    <canvas id="metrics-bar-chart"></canvas>
                </div>
            </div>
        </div>

        <div class="logs-section">
            <div class="logs-header">
                <h3>Logs</h3>
                <div class="logs-controls">
                    <button id="show-log-files">Log Files</button>
                    <button id="refresh-logs">Refresh</button>
                    <button id="toggle-logs">Show Logs</button>
                </div>
            </div>
            <div id="log-files-list" class="logs-hidden">
                <div class="log-files-content"></div>
            </div>
            <div id="logs-content" class="logs-hidden">
                <div class="logs-text"></div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/marked@11.1.1/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="assets/app.js"></script>
</body>
</html>
"""

    html_path = os.path.join(viewer_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def create_stylesheet(assets_dir: str) -> None:
    """Create style.css file.

    Args:
        assets_dir: Assets directory path
    """
    css_content = """/* Pasture Viewer - Minimalist CSS */

:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f6f6f6;
    --bg-hover: #e8e8e8;
    --text-primary: #000000;
    --text-secondary: #666666;
    --border: #cccccc;
    --accent: #ff6600;
    --calendar-today: #ffffcc;
    --calendar-has-content: #e6f3ff;
}

[data-theme="dark"] {
    --bg-primary: #1a1a1a;
    --bg-secondary: #2a2a2a;
    --bg-hover: #3a3a3a;
    --text-primary: #e0e0e0;
    --text-secondary: #a0a0a0;
    --border: #444444;
    --accent: #ff6600;
    --calendar-today: #3a3a00;
    --calendar-has-content: #1a2a3a;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Verdana', 'Geneva', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    background: var(--bg-primary);
    color: var(--text-primary);
    transition: background 0.3s, color 0.3s;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 20px;
    border-bottom: 2px solid var(--accent);
    margin-bottom: 20px;
}

header h1 {
    font-size: 24px;
    font-weight: bold;
    color: var(--accent);
}

.header-controls {
    display: flex;
    gap: 10px;
}

.header-controls button {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 8px 12px;
    cursor: pointer;
    font-size: 18px;
    transition: background 0.2s;
}

.header-controls button:hover {
    background: var(--bg-hover);
}

.calendar-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}

.calendar-overlay.active {
    display: flex;
}

.calendar-container {
    background: var(--bg-secondary);
    padding: 20px;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.settings-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}

.settings-overlay.active {
    display: flex;
}

.settings-container {
    background: var(--bg-secondary);
    padding: 25px;
    border-radius: 8px;
    max-width: 800px;
    width: 90%;
    max-height: 85vh;
    overflow-y: auto;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.settings-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid var(--border);
}

.settings-header h2 {
    font-size: 22px;
    color: var(--accent);
    margin: 0;
}

.settings-header button {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 5px 10px;
    cursor: pointer;
    font-size: 20px;
    transition: background 0.2s;
}

.settings-header button:hover {
    background: var(--bg-hover);
}

.settings-content h3 {
    font-size: 16px;
    margin-bottom: 10px;
    color: var(--text-primary);
}

.config-editor {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 15px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
    color: var(--text-primary);
    width: 100%;
    min-height: 400px;
    resize: vertical;
    box-sizing: border-box;
}

.config-editor:focus {
    outline: none;
    border-color: var(--accent);
}

.settings-actions {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-top: 15px;
}

.save-button {
    background: var(--accent);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: bold;
    transition: opacity 0.2s;
}

.save-button:hover {
    opacity: 0.9;
}

.save-button:active {
    opacity: 0.8;
}

.save-status {
    font-size: 14px;
    color: var(--text-secondary);
}

.save-status.success {
    color: #4caf50;
}

.save-status.error {
    color: #f44336;
}

.calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.calendar-header button {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    padding: 5px 15px;
    cursor: pointer;
    border-radius: 3px;
    font-size: 16px;
    transition: background 0.2s;
}

.calendar-header button:hover {
    background: var(--bg-hover);
}

.calendar-header h2 {
    font-size: 18px;
}

#calendar {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 3px;
    width: 100%;
}

.calendar-day {
    aspect-ratio: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 3px;
    cursor: pointer;
    transition: background 0.2s;
    font-size: 12px;
    min-height: 40px;
}

.calendar-day.header {
    font-weight: bold;
    cursor: default;
    background: var(--bg-secondary);
}

.calendar-day.empty {
    cursor: default;
    opacity: 0.3;
}

.calendar-day.today {
    background: var(--calendar-today);
    font-weight: bold;
}

.calendar-day.has-content {
    background: var(--calendar-has-content);
    font-weight: bold;
}

.calendar-day.selected {
    background: var(--accent);
    color: white;
}

.calendar-day:not(.header):not(.empty):hover {
    background: var(--bg-hover);
}

.source-filters {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.filter-btn {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    padding: 6px 12px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 13px;
    transition: background 0.2s, color 0.2s;
}

.filter-btn:hover {
    background: var(--bg-hover);
}

.filter-btn.active {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
}

.main-content {
    display: grid;
    grid-template-columns: 350px 1fr;
    gap: 20px;
    min-height: 600px;
}

.timeline {
    background: var(--bg-secondary);
    border-radius: 4px;
    padding: 15px;
    overflow-y: auto;
    max-height: 800px;
}

.article-item {
    padding: 12px;
    margin-bottom: 10px;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 3px;
    cursor: pointer;
    transition: background 0.2s;
    overflow: hidden;
}

.article-item:hover {
    background: var(--bg-hover);
}

.article-item.selected {
    border-color: var(--accent);
    border-width: 2px;
}

.article-item .article-source {
    font-size: 11px;
    color: var(--text-secondary);
    text-transform: uppercase;
    margin-bottom: 5px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.article-item .article-title {
    font-weight: bold;
    margin-bottom: 5px;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.article-item .article-preview {
    font-size: 12px;
    color: var(--text-secondary);
    line-height: 1.4;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

.viewer {
    background: var(--bg-secondary);
    border-radius: 4px;
    padding: 30px;
    overflow-y: auto;
    max-height: 800px;
}

.welcome {
    text-align: center;
    padding: 100px 20px;
    color: var(--text-secondary);
}

#article-content h1 {
    font-size: 28px;
    margin-bottom: 20px;
    color: var(--text-primary);
}

#article-content h2 {
    font-size: 22px;
    margin-top: 25px;
    margin-bottom: 15px;
    color: var(--text-primary);
}

#article-content h3 {
    font-size: 18px;
    margin-top: 20px;
    margin-bottom: 10px;
    color: var(--text-primary);
}

#article-content p {
    margin-bottom: 15px;
    line-height: 1.7;
}

#article-content ul,
#article-content ol {
    margin-bottom: 15px;
    margin-left: 25px;
}

#article-content li {
    margin-bottom: 8px;
    line-height: 1.6;
}

#article-content pre {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 15px;
    overflow-x: auto;
    margin-bottom: 15px;
}

#article-content code {
    background: var(--bg-primary);
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
}

#article-content pre code {
    background: none;
    padding: 0;
}

#article-content a {
    color: var(--accent);
    text-decoration: none;
}

#article-content a:hover {
    text-decoration: underline;
}

#article-content blockquote {
    border-left: 3px solid var(--accent);
    padding-left: 15px;
    margin: 15px 0;
    color: var(--text-secondary);
    font-style: italic;
}

.loading {
    text-align: center;
    padding: 50px;
    color: var(--text-secondary);
}

.error {
    text-align: center;
    padding: 50px;
    color: #cc0000;
}

.stats-section {
    margin-top: 30px;
    background: var(--bg-secondary);
    padding: 20px;
    border-radius: 4px;
}

.stats-section h3 {
    margin-bottom: 15px;
    font-size: 18px;
    color: var(--text-primary);
}

.stats-placeholder {
    color: var(--text-secondary);
    font-style: italic;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}

.stat-card {
    background: var(--bg-primary);
    padding: 15px;
    border-radius: 4px;
    border: 1px solid var(--border);
}

.stat-label {
    font-size: 12px;
    color: var(--text-secondary);
    text-transform: uppercase;
    margin-bottom: 5px;
}

.stat-value {
    font-size: 32px;
    font-weight: bold;
    color: var(--accent);
}

.stat-breakdown {
    margin-top: 10px;
    font-size: 13px;
}

.stat-breakdown-scroll {
    max-height: 150px;
    overflow-y: auto;
    padding-right: 5px;
}

.stat-breakdown-scroll::-webkit-scrollbar {
    width: 6px;
}

.stat-breakdown-scroll::-webkit-scrollbar-track {
    background: var(--bg-secondary);
    border-radius: 3px;
}

.stat-breakdown-scroll::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 3px;
}

.stat-breakdown-scroll::-webkit-scrollbar-thumb:hover {
    background: var(--text-secondary);
}

.stat-breakdown-item {
    display: flex;
    justify-content: space-between;
    padding: 3px 0;
    color: var(--text-secondary);
}

#stats-charts {
    margin-top: 20px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
    transition: max-height 0.3s ease;
}

#stats-charts.stats-charts-hidden {
    display: none;
}

.chart-container {
    background: var(--bg-primary);
    padding: 20px;
    border-radius: 4px;
    border: 1px solid var(--border);
}

.chart-container h4 {
    margin-bottom: 15px;
    font-size: 16px;
    color: var(--text-primary);
    text-align: center;
}

.chart-container canvas {
    max-height: 300px;
}

.logs-section {
    margin-top: 30px;
    background: var(--bg-secondary);
    padding: 20px;
    border-radius: 4px;
}

.logs-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.logs-header h3 {
    font-size: 18px;
    color: var(--text-primary);
    margin: 0;
}

.logs-controls {
    display: flex;
    gap: 10px;
}

.logs-controls button {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    padding: 6px 12px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 13px;
    transition: background 0.2s;
}

.logs-controls button:hover {
    background: var(--bg-hover);
}

#logs-content {
    max-height: 400px;
    overflow-y: auto;
    transition: max-height 0.3s ease;
}

#logs-content.logs-hidden {
    max-height: 0;
    overflow: hidden;
}

.logs-text {
    background: var(--bg-primary);
    padding: 15px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.4;
    white-space: pre-wrap;
    word-wrap: break-word;
    color: var(--text-primary);
}

.log-line {
    margin-bottom: 2px;
}

.log-info {
    color: #4a9eff;
}

.log-warning {
    color: #ffa500;
}

.log-error {
    color: #ff4444;
}

#log-files-list {
    max-height: 300px;
    overflow-y: auto;
    transition: max-height 0.3s ease;
    margin-bottom: 10px;
}

#log-files-list.logs-hidden {
    max-height: 0;
    overflow: hidden;
}

.log-files-content {
    background: var(--bg-primary);
    padding: 15px;
    border-radius: 3px;
}

.log-file-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
}

.log-file-item:last-child {
    border-bottom: none;
}

.log-file-name {
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: var(--text-primary);
}

.log-file-size {
    font-size: 12px;
    color: var(--text-secondary);
    margin-left: 10px;
}

.log-file-download {
    background: var(--accent);
    color: white;
    border: none;
    padding: 4px 10px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 12px;
    transition: opacity 0.2s;
}

.log-file-download:hover {
    opacity: 0.8;
}

@media (max-width: 768px) {
    header h1 {
        font-size: 20px;
    }

    .calendar-container {
        max-width: 100%;
    }

    .main-content {
        grid-template-columns: 1fr;
        gap: 10px;
    }

    .timeline {
        max-height: 300px;
        order: 2;
    }

    .viewer {
        max-height: none;
        order: 1;
        min-height: 400px;
    }

    .stats-grid {
        grid-template-columns: 1fr;
    }

    .logs-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }

    .logs-controls {
        width: 100%;
    }

    .logs-controls button {
        flex: 1;
    }
}
"""

    css_path = os.path.join(assets_dir, "style.css")
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css_content)


def create_javascript(assets_dir: str) -> None:
    """Create app.js file.

    Args:
        assets_dir: Assets directory path
    """
    js_content = """// Pasture Viewer - Main Application

// State
const state = {
    indexData: null,
    currentDate: null,
    currentMonth: new Date(),
    selectedSource: 'all',
    selectedArticle: null,
    datesWithContent: new Set()
};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    setupTheme();
    await loadIndex();
    renderCalendar();
    setupEventListeners();
});

// Theme Management
function setupTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    document.getElementById('theme-toggle').addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    });

    // Calendar overlay toggle
    const calendarOverlay = document.getElementById('calendar-overlay');
    const calendarToggle = document.getElementById('calendar-toggle');

    calendarToggle.addEventListener('click', () => {
        calendarOverlay.classList.toggle('active');
    });

    // Close calendar when clicking outside
    calendarOverlay.addEventListener('click', (e) => {
        if (e.target === calendarOverlay) {
            calendarOverlay.classList.remove('active');
        }
    });

    // Close calendar when a date is selected
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('calendar-day') && e.target.classList.contains('has-content')) {
            calendarOverlay.classList.remove('active');
        }
    });

    // Settings overlay toggle
    const settingsOverlay = document.getElementById('settings-overlay');
    const settingsToggle = document.getElementById('settings-toggle');
    const settingsClose = document.getElementById('settings-close');

    settingsToggle.addEventListener('click', async () => {
        settingsOverlay.classList.add('active');
        await loadConfig();
    });

    settingsClose.addEventListener('click', () => {
        settingsOverlay.classList.remove('active');
    });

    // Close settings when clicking outside
    settingsOverlay.addEventListener('click', (e) => {
        if (e.target === settingsOverlay) {
            settingsOverlay.classList.remove('active');
        }
    });

    // Save config button
    const saveButton = document.getElementById('save-config');
    saveButton.addEventListener('click', async () => {
        await saveConfig();
    });
}

async function loadConfig() {
    const configContent = document.getElementById('config-content');
    const saveStatus = document.getElementById('save-status');
    saveStatus.textContent = '';
    saveStatus.className = 'save-status';

    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        if (data.success) {
            configContent.value = data.content;
        } else {
            configContent.value = 'Error loading configuration: ' + (data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Failed to load config:', error);
        configContent.value = 'Error loading configuration: ' + error.message;
    }
}

async function saveConfig() {
    const configContent = document.getElementById('config-content');
    const saveButton = document.getElementById('save-config');
    const saveStatus = document.getElementById('save-status');

    const content = configContent.value;

    // Disable button while saving
    saveButton.disabled = true;
    saveButton.textContent = 'Saving...';
    saveStatus.textContent = '';
    saveStatus.className = 'save-status';

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: content })
        });

        const data = await response.json();

        if (data.success) {
            saveStatus.textContent = '✓ Configuration saved successfully!';
            saveStatus.className = 'save-status success';
        } else {
            saveStatus.textContent = '✗ Error: ' + (data.error || 'Unknown error');
            saveStatus.className = 'save-status error';
        }
    } catch (error) {
        console.error('Failed to save config:', error);
        saveStatus.textContent = '✗ Error saving: ' + error.message;
        saveStatus.className = 'save-status error';
    } finally {
        saveButton.disabled = false;
        saveButton.textContent = 'Save Changes';

        // Clear status after 5 seconds
        setTimeout(() => {
            saveStatus.textContent = '';
        }, 5000);
    }
}

// Data Loading
async function loadIndex() {
    try {
        const response = await fetch('data/index.json');
        state.indexData = await response.json();

        // Populate dates with content
        state.indexData.dates.forEach(d => {
            state.datesWithContent.add(d.date);
        });

        // Populate source filters
        renderSourceFilters();

        // Select most recent date if available
        if (state.indexData.dates.length > 0) {
            await selectDate(state.indexData.dates[0].date);
        }
    } catch (error) {
        console.error('Failed to load index:', error);
        showError('Failed to load content index');
    }
}

async function loadDailyData(date) {
    try {
        const response = await fetch(`data/${date}.json`);
        return await response.json();
    } catch (error) {
        console.error(`Failed to load data for ${date}:`, error);
        return null;
    }
}

async function loadArticle(filePath) {
    try {
        const response = await fetch(filePath);
        return await response.text();
    } catch (error) {
        console.error(`Failed to load article ${filePath}:`, error);
        return null;
    }
}

// Calendar Rendering
function renderCalendar() {
    const calendar = document.getElementById('calendar');
    const monthHeader = document.getElementById('current-month');

    const year = state.currentMonth.getFullYear();
    const month = state.currentMonth.getMonth();

    monthHeader.textContent = state.currentMonth.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
    });

    calendar.innerHTML = '';

    // Day headers
    ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(day => {
        const header = document.createElement('div');
        header.className = 'calendar-day header';
        header.textContent = day;
        calendar.appendChild(header);
    });

    // Get first day of month and days in month
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {
        const empty = document.createElement('div');
        empty.className = 'calendar-day empty';
        calendar.appendChild(empty);
    }

    // Days of month
    const today = new Date();
    const todayStr = formatDate(today);

    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dateStr = formatDate(date);

        const dayCell = document.createElement('div');
        dayCell.className = 'calendar-day';
        dayCell.textContent = day;
        dayCell.dataset.date = dateStr;

        if (dateStr === todayStr) {
            dayCell.classList.add('today');
        }

        if (state.datesWithContent.has(dateStr)) {
            dayCell.classList.add('has-content');
            dayCell.addEventListener('click', () => selectDate(dateStr));
        } else {
            dayCell.classList.add('empty');
        }

        if (dateStr === state.currentDate) {
            dayCell.classList.add('selected');
        }

        calendar.appendChild(dayCell);
    }
}

function renderSourceFilters() {
    const container = document.querySelector('.source-filters');

    // Clear except "All" button
    while (container.children.length > 1) {
        container.removeChild(container.lastChild);
    }

    // Add source buttons
    if (state.indexData && state.indexData.sources) {
        state.indexData.sources.forEach(source => {
            const button = document.createElement('button');
            button.className = 'filter-btn';
            button.dataset.source = source;
            button.textContent = source;
            button.addEventListener('click', () => filterBySource(source));
            container.appendChild(button);
        });
    }
}

async function selectDate(date) {
    state.currentDate = date;

    // Update calendar
    document.querySelectorAll('.calendar-day').forEach(cell => {
        cell.classList.remove('selected');
        if (cell.dataset.date === date) {
            cell.classList.add('selected');
        }
    });

    // Load and render articles
    const dailyData = await loadDailyData(date);
    if (dailyData) {
        renderArticleList(dailyData.articles);
        renderStats(dailyData);
    }
}

function renderArticleList(articles) {
    const container = document.getElementById('article-list');
    container.innerHTML = '';

    // Filter by source
    let filtered = articles;
    if (state.selectedSource !== 'all') {
        filtered = articles.filter(a => a.source === state.selectedSource);
    }

    if (filtered.length === 0) {
        container.innerHTML = '<div class="loading">No articles found</div>';
        return;
    }

    filtered.forEach(article => {
        const item = document.createElement('div');
        item.className = 'article-item';
        item.dataset.id = article.id;

        item.innerHTML = `
            <div class="article-source">${article.source}</div>
            <div class="article-title">${escapeHtml(article.title)}</div>
            <div class="article-preview">${escapeHtml(article.preview)}</div>
        `;

        item.addEventListener('click', () => selectArticle(article));
        container.appendChild(item);
    });
}

async function selectArticle(article) {
    state.selectedArticle = article;

    // Update selection in list
    document.querySelectorAll('.article-item').forEach(item => {
        item.classList.remove('selected');
        if (item.dataset.id === article.id) {
            item.classList.add('selected');
        }
    });

    // Load and render article content
    const viewer = document.getElementById('article-content');
    viewer.innerHTML = '<div class="loading">Loading article...</div>';

    const content = await loadArticle(article.file_path);
    if (content) {
        const html = marked.parse(content);
        viewer.innerHTML = html;
    } else {
        viewer.innerHTML = '<div class="error">Failed to load article</div>';
    }
}

function filterBySource(source) {
    state.selectedSource = source;

    // Update button states
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.source === source) {
            btn.classList.add('active');
        }
    });

    // Re-render article list
    if (state.currentDate) {
        loadDailyData(state.currentDate).then(dailyData => {
            if (dailyData) {
                renderArticleList(dailyData.articles);
            }
        });
    }
}

async function renderStats(dailyData) {
    const container = document.getElementById('stats-content');
    const chartsContainer = document.getElementById('stats-charts');

    if (!dailyData || !dailyData.articles || dailyData.articles.length === 0) {
        container.innerHTML = '<p class="stats-placeholder">No data for this date</p>';
        chartsContainer.classList.add('stats-charts-hidden');
        return;
    }

    const articles = dailyData.articles;
    const totalArticles = articles.length;

    // Count by source
    const bySource = {};
    articles.forEach(article => {
        bySource[article.source] = (bySource[article.source] || 0) + 1;
    });

    // Sort sources by count
    const sortedSources = Object.entries(bySource).sort((a, b) => b[1] - a[1]);

    // Calculate total preview length (rough content size indicator)
    const totalChars = articles.reduce((sum, a) => sum + (a.preview ? a.preview.length : 0), 0);
    const avgChars = Math.round(totalChars / totalArticles);

    // Fetch stats data for this date
    let statsData = null;
    try {
        const response = await fetch(`/api/stats?date=${dailyData.date}`);
        const data = await response.json();
        if (data.has_data) {
            statsData = data.stats;
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }

    // Build stats HTML
    let statsHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Articles</div>
                <div class="stat-value">${totalArticles}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Sources Active</div>
                <div class="stat-value">${Object.keys(bySource).length}</div>
                <div class="stat-breakdown stat-breakdown-scroll">
                    ${sortedSources.map(([source, count]) => `
                        <div class="stat-breakdown-item">
                            <span>${source}</span>
                            <span>${count}</span>
                        </div>
                    `).join('')}
                </div>
            </div>`;

    if (statsData) {
        // Calculate rejection rate: rejected / (scraped + rejected + duplicates)
        const totalPosts = (statsData.articles_scraped || 0) + (statsData.articles_rejected_blacklist || 0) + (statsData.articles_skipped_duplicate || 0);
        const rejectionRate = totalPosts > 0
            ? ((statsData.articles_rejected_blacklist / totalPosts) * 100).toFixed(1)
            : 0;

        statsHTML += `
            <div class="stat-card">
                <div class="stat-label">Blacklist Rejections</div>
                <div class="stat-value">${statsData.articles_rejected_blacklist || 0}</div>
                <div class="stat-breakdown">
                    <div class="stat-breakdown-item">
                        <span>Rejection rate</span>
                        <span>${rejectionRate}%</span>
                    </div>
                </div>
            </div>`;

        // Blacklist terms
        if (statsData.blacklist_hits_by_term && Object.keys(statsData.blacklist_hits_by_term).length > 0) {
            const allTerms = Object.entries(statsData.blacklist_hits_by_term)
                .sort((a, b) => b[1] - a[1]);

            statsHTML += `
            <div class="stat-card">
                <div class="stat-label">Blacklist Terms</div>
                <div class="stat-value">${allTerms.length}</div>
                <div class="stat-breakdown stat-breakdown-scroll">
                    ${allTerms.map(([term, count]) => `
                        <div class="stat-breakdown-item">
                            <span>${escapeHtml(term)}</span>
                            <span>${count}</span>
                        </div>
                    `).join('')}
                </div>
            </div>`;
        }
    }

    statsHTML += `</div>`;
    container.innerHTML = statsHTML;

    // Render charts
    chartsContainer.classList.remove('stats-charts-hidden');
    renderCharts(bySource, statsData);
}

let radarChart = null;
let barChart = null;

function renderCharts(bySource, statsData) {
    // Destroy existing charts
    if (radarChart) {
        radarChart.destroy();
    }
    if (barChart) {
        barChart.destroy();
    }

    // Theme colors
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#e0e0e0' : '#000000';
    const gridColor = isDark ? '#444444' : '#cccccc';

    // Radar chart - Source distribution
    const radarCtx = document.getElementById('source-radar-chart').getContext('2d');
    const sources = Object.keys(bySource);
    const counts = Object.values(bySource);

    radarChart = new Chart(radarCtx, {
        type: 'radar',
        data: {
            labels: sources,
            datasets: [{
                label: 'Articles per Source',
                data: counts,
                backgroundColor: 'rgba(255, 102, 0, 0.2)',
                borderColor: 'rgba(255, 102, 0, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(255, 102, 0, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(255, 102, 0, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: textColor
                    }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor
                    },
                    pointLabels: {
                        color: textColor
                    }
                }
            }
        }
    });

    // Pie chart - Metrics comparison
    if (statsData) {
        const pieCtx = document.getElementById('metrics-bar-chart').getContext('2d');

        barChart = new Chart(pieCtx, {
            type: 'pie',
            data: {
                labels: ['Scraped', 'Rejected'],
                datasets: [{
                    data: [
                        statsData.articles_scraped || 0,
                        statsData.articles_rejected_blacklist || 0
                    ],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(255, 99, 132, 0.7)'
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 99, 132, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: textColor,
                            padding: 15,
                            font: {
                                size: 13
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }
}

async function loadLogs() {
    const logsText = document.querySelector('.logs-text');
    logsText.innerHTML = '<div class="loading">Loading logs...</div>';

    try {
        const response = await fetch('/api/logs');
        const logs = await response.text();

        // Format logs with syntax highlighting
        const formattedLogs = logs.split('\\n').map(line => {
            let className = 'log-line';
            if (line.includes('ERROR') || line.includes('❌')) {
                className += ' log-error';
            } else if (line.includes('WARNING') || line.includes('⚠️')) {
                className += ' log-warning';
            } else if (line.includes('INFO') || line.includes('✅') || line.includes('📊')) {
                className += ' log-info';
            }
            return `<div class="${className}">${escapeHtml(line)}</div>`;
        }).join('');

        logsText.innerHTML = formattedLogs || '<div class="stats-placeholder">No logs available</div>';

        // Auto-scroll to bottom
        const logsContent = document.getElementById('logs-content');
        logsContent.scrollTop = logsContent.scrollHeight;
    } catch (error) {
        logsText.innerHTML = '<div class="error">Failed to load logs</div>';
        console.error('Failed to load logs:', error);
    }
}

function setupEventListeners() {
    document.getElementById('prev-month').addEventListener('click', () => {
        state.currentMonth.setMonth(state.currentMonth.getMonth() - 1);
        renderCalendar();
    });

    document.getElementById('next-month').addEventListener('click', () => {
        state.currentMonth.setMonth(state.currentMonth.getMonth() + 1);
        renderCalendar();
    });

    document.querySelector('[data-source="all"]').addEventListener('click', () => {
        filterBySource('all');
    });

    // Logs controls
    document.getElementById('toggle-logs').addEventListener('click', () => {
        const logsContent = document.getElementById('logs-content');
        const toggleBtn = document.getElementById('toggle-logs');

        if (logsContent.classList.contains('logs-hidden')) {
            logsContent.classList.remove('logs-hidden');
            toggleBtn.textContent = 'Hide Logs';
            loadLogs();
        } else {
            logsContent.classList.add('logs-hidden');
            toggleBtn.textContent = 'Show Logs';
        }
    });

    document.getElementById('refresh-logs').addEventListener('click', () => {
        if (!document.getElementById('logs-content').classList.contains('logs-hidden')) {
            loadLogs();
        }
    });

    // Log files list toggle
    document.getElementById('show-log-files').addEventListener('click', () => {
        const logFilesList = document.getElementById('log-files-list');
        const toggleBtn = document.getElementById('show-log-files');

        if (logFilesList.classList.contains('logs-hidden')) {
            logFilesList.classList.remove('logs-hidden');
            toggleBtn.textContent = 'Hide Files';
            loadLogFilesList();
        } else {
            logFilesList.classList.add('logs-hidden');
            toggleBtn.textContent = 'Log Files';
        }
    });
}

async function loadLogFilesList() {
    const container = document.querySelector('.log-files-content');
    container.innerHTML = '<div class="loading">Loading log files...</div>';

    try {
        const response = await fetch('/api/logs/list');
        const logFiles = await response.json();

        if (logFiles.length === 0) {
            container.innerHTML = '<div class="stats-placeholder">No log files available</div>';
            return;
        }

        const formatSize = (bytes) => {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        };

        const html = logFiles.map(file => `
            <div class="log-file-item">
                <div>
                    <span class="log-file-name">${escapeHtml(file.name)}</span>
                    <span class="log-file-size">${formatSize(file.size)}</span>
                </div>
                <button class="log-file-download" onclick="window.open('${file.url}', '_blank')">
                    Download
                </button>
            </div>
        `).join('');

        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<div class="error">Failed to load log files</div>';
        console.error('Failed to load log files:', error);
    }
}

// Utilities
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    const viewer = document.getElementById('article-content');
    viewer.innerHTML = `<div class="error">${message}</div>`;
}
"""

    js_path = os.path.join(assets_dir, "app.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_content)


def start_http_server(output_base_dir: str, port: int = 8000) -> None:
    """Start HTTP server to serve the web viewer.

    Args:
        output_base_dir: Base output directory
        port: Port to serve on (default: 8000)
    """
    viewer_dir = os.path.join(output_base_dir, "viewer")

    # Always regenerate viewer on startup to pick up any code changes
    logger.info("Generating web viewer on startup...")
    generate_static_site(output_base_dir)

    # Serve from output_base_dir so both viewer/ and markdown files are accessible
    class ViewerHTTPRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=output_base_dir, **kwargs)

        def do_GET(self):
            # Redirect root to /viewer/
            if self.path == '/':
                self.send_response(301)
                self.send_header('Location', '/viewer/')
                self.end_headers()
                return

            # Logs API endpoints
            if self.path == '/api/logs':
                try:
                    # Read from the current rotating log file
                    log_file = os.path.join(output_base_dir, 'logs', 'scraper.log')

                    if os.path.exists(log_file):
                        # Read last 500 lines
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            logs = ''.join(lines[-500:])
                    else:
                        logs = "Log file not available."

                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(logs.encode('utf-8'))
                except Exception as e:
                    logger.error(f"Failed to fetch logs: {e}")
                    self.send_response(500)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error fetching logs: {str(e)}".encode('utf-8'))
                return

            # List log files
            if self.path == '/api/logs/list':
                try:
                    logs_dir = os.path.join(output_base_dir, 'logs')
                    log_files = []

                    if os.path.exists(logs_dir):
                        files_list = []
                        for filename in os.listdir(logs_dir):
                            if filename.endswith('.log') or filename.startswith('scraper.log.'):
                                filepath = os.path.join(logs_dir, filename)
                                size = os.path.getsize(filepath)
                                # Mark the current log file
                                display_name = filename
                                if filename == 'scraper.log':
                                    display_name = 'scraper.log (current)'
                                files_list.append({
                                    'name': display_name,
                                    'size': size,
                                    'url': f'/api/logs/download/{filename}',
                                    'filename': filename
                                })

                        # Sort: current first, then by date descending
                        files_list.sort(key=lambda x: (
                            0 if x['filename'] == 'scraper.log' else 1,
                            -os.path.getmtime(os.path.join(logs_dir, x['filename']))
                        ))
                        log_files = files_list

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(log_files).encode('utf-8'))
                except Exception as e:
                    logger.error(f"Failed to list logs: {e}")
                    self.send_response(500)
                    self.end_headers()
                return

            # Config API endpoint
            if self.path == '/api/config':
                try:
                    config_file = 'config.ini'
                    if os.path.exists(config_file):
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config_content = f.read()

                        response_data = {
                            'success': True,
                            'content': config_content
                        }
                    else:
                        response_data = {
                            'success': False,
                            'error': 'Configuration file not found'
                        }

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                except Exception as e:
                    logger.error(f"Failed to load config: {e}")
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    error_data = {
                        'success': False,
                        'error': str(e)
                    }
                    self.wfile.write(json.dumps(error_data).encode('utf-8'))
                return

            # Stats API endpoint
            if self.path.startswith('/api/stats'):
                try:
                    # Parse date from query string if provided
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(self.path)
                    query_params = parse_qs(parsed.query)
                    date_param = query_params.get('date', [None])[0]

                    stats_file = os.path.join(output_base_dir, 'stats.json')
                    if os.path.exists(stats_file):
                        with open(stats_file, 'r', encoding='utf-8') as f:
                            all_stats = json.load(f)

                        # If date specified, return daily stats for that date
                        if date_param and 'daily' in all_stats and date_param in all_stats['daily']:
                            response_data = {
                                'date': date_param,
                                'stats': all_stats['daily'][date_param],
                                'has_data': True
                            }
                        else:
                            # Return overall stats
                            response_data = {
                                'daily': all_stats.get('daily', {}),
                                'recent_sessions': all_stats.get('sessions', [])[-10:],
                                'has_data': True
                            }
                    else:
                        response_data = {'has_data': False, 'message': 'No stats available yet'}

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                except Exception as e:
                    logger.error(f"Failed to fetch stats: {e}")
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return

            # Download specific log file
            if self.path.startswith('/api/logs/download/'):
                try:
                    filename = self.path.split('/')[-1]
                    log_file = os.path.join(output_base_dir, 'logs', filename)

                    if os.path.exists(log_file):
                        with open(log_file, 'rb') as f:
                            content = f.read()

                        self.send_response(200)
                        self.send_header('Content-Type', 'text/plain; charset=utf-8')
                        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(content)
                    else:
                        self.send_response(404)
                        self.end_headers()
                except Exception as e:
                    logger.error(f"Failed to download log: {e}")
                    self.send_response(500)
                    self.end_headers()
                return

            super().do_GET()

        def do_POST(self):
            # Config save endpoint
            if self.path == '/api/config':
                try:
                    # Get content length
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))

                    # Get the new config content
                    new_content = data.get('content', '')

                    # Save to config.ini
                    config_file = 'config.ini'
                    with open(config_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    # Trigger config reload in main thread
                    try:
                        from core.config_reload import trigger_config_reload
                        trigger_config_reload()
                        logger.info("Configuration saved and reload triggered")
                    except Exception as e:
                        logger.warning(f"Config saved but reload trigger failed: {e}")

                    response_data = {
                        'success': True,
                        'message': 'Configuration saved successfully'
                    }

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                except Exception as e:
                    logger.error(f"Failed to save config: {e}")
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    error_data = {
                        'success': False,
                        'error': str(e)
                    }
                    self.wfile.write(json.dumps(error_data).encode('utf-8'))
                return

            # Return 404 for other POST requests
            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            # Suppress HTTP server logs to keep output clean
            pass

    def run_server():
        try:
            server = HTTPServer(("0.0.0.0", port), ViewerHTTPRequestHandler)
            logger.info(f"📊 Web viewer available at http://localhost:{port}")
            server.serve_forever()
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")

    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    logger.info(f"🌐 HTTP server started on port {port}")
