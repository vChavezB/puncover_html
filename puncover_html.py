# Copyright 2022, Victor Chavez (chavez-bermudez@fh-aachen.de)
# SPDX-License-Identifier: GPL-3.0-or-later
import requests
import pathlib
import re
import os
import argparse
import distutils.dir_util

url_base = "http://127.0.0.1:5000/"

parser = argparse.ArgumentParser(
                    prog = 'Puncover offline HTML',
                    description = 'Builds offline html for puncover',
                    )
parser.add_argument('dir_out')
args = parser.parse_args()

script_root = pathlib.Path(__file__).resolve().parents[0]
dir_out = pathlib.Path(args.dir_out)
dir_out.mkdir(parents=True, exist_ok=True)
parsed_pages = []
puncover_links = []
pending_links = []

def replace_static_path(html_raw):
    return html_raw.replace("/static", "static")


def replace_html_encode(content):
    content = content.replace("%3E", "_")
    content = content.replace("%3C", "_")
    content = content.replace("%5C", "_")
    content = content.replace("%5", "_")
    return content


def get_links(html_content):
    links = []
    for match in re.finditer('<a href="/path/', html_content):
        path_start = match.end()
        path_end = html_content[path_start:].find('"')
        parsed_path = html_content[path_start:path_start + path_end]
        links.append("/path/" + parsed_path)
    if html_content.find('/all/') != -1:
        links.append('/all/')
    return links


def fix_sort_table(html_str):
    thead_start = html_str.find("<thead>")
    if thead_start == -1:
        return None
    thead_end = html_str.find("</thead>")
    tfoot_start = html_str.find("<tfoot>")
    if tfoot_start == -1:
        return None
    html_content = html_str.replace('table-bordered', 'table-bordered sortable')
    thead_simple = """<thead><tr>
                        <th width="100%">Name</th>
                        <th>Remarks</th>
                        <th>Stack</th>
                        <th>Code</th>
                        <th>Static</th>
                        </tr>
                        </thead>
			        """
    html_content = html_content[:thead_start] + thead_simple + html_content[thead_end:]
    title_start = html_content.find("<title>")
    sort_script = '\n<script src="../static/js/sorttable.js"></script>\n'
    html_content = html_content[:title_start] + sort_script + html_content[title_start:]

    bottom_row_regex = r"<tr>\n +<th.colspan=\"[0-9]\">&sum"
    tr_modification = '<tr class="sortbottom">'
    match_res = re.finditer(bottom_row_regex, html_content, re.MULTILINE)
    if match_res is not None:
        total_bottom_rows = sum(1 for e in match_res)
        for i in range(0, total_bottom_rows):
            regex_res = re.search(bottom_row_regex, html_content)
            tr_start = regex_res.start()
            html_content = html_content[:tr_start] + tr_modification+ html_content[tr_start+len("<tr>"):]

    return html_content


def generate_html(link):
    if link in puncover_links:
        return None
    puncover_links.append(link)
    paged_parsed = False
    for page in parsed_pages:
        if page["puncover_url"] == link[:-1]:
            paged_parsed = True
            break
    if paged_parsed:
        return
    r = requests.get(url_base + link)
    html_content = r.text
    table_html = fix_sort_table(html_content)
    if table_html is not None:
        html_content = table_html
    # add relative paths
    if "/all/" not in link:
        html_content = html_content.replace('src="/static', 'src="../static')
        html_content = html_content.replace('href="/static', 'href="../static')
        html_content = html_content.replace('href="/"', 'href="../index.html"')
    else:
        # due to fix_sort_table already adding .. to static
        html_content = html_content.replace('src="../static', 'src="static') 
        html_content = html_content.replace('href="../static','href="static')
        html_content = html_content.replace('href="/"', 'href="index.html"')
    html_file_name = replace_html_encode(link[:-1])+".html"
    if html_file_name.startswith("/"):
        html_file_name=html_file_name[1:]
        
    if html_file_name.startswith("path/"):
        compact_path = html_file_name[len("path/"):].replace("/","_")
        html_file_name = "path/"+compact_path

    html_file_path = dir_out.joinpath(html_file_name)
    # Create dirs for html page if they do not exist
    html_file_path.parents[0].mkdir(parents=True, exist_ok=True)
    new_html = open(html_file_path, 'w+')
    new_html.write(html_content)
    new_html.close()
    page_info = {"file": html_file_path, "puncover_url": link[:-1]}
    if page_info not in parsed_pages:
        parsed_pages.append(page_info)
    possible_links = get_links(html_content)
    new_links = []
    for plink in possible_links:
        if plink not in puncover_links:
            new_links.append(plink)
    return new_links


def process_link(link):
    new_links = generate_html(link)
    if new_links is not None:
        pending_links.extend(new_links)


def get_local_html(puncover_url):
    for info in parsed_pages:
        if info["puncover_url"] == puncover_url:
            return info["file"]
    return None


def local_html():
    print("Processing main page")
    pages_dir = dir_out.joinpath("path")
    static_dir = dir_out.joinpath("static")
    if not os.path.exists(dir_out):
        os.makedirs(dir_out)
    if not os.path.exists(pages_dir):
        os.makedirs(pages_dir)
    if not os.path.exists(static_dir):
        os.makedirs(static_dir) 
    # Copy html static dir (css,js,etc) to output
    distutils.dir_util.copy_tree(str(script_root.joinpath("static")),
                                    str(static_dir))
    index = requests.get(url_base)
    index_html_path = dir_out.joinpath("index.html")
    index_file = open(index_html_path, "w+")
    html_content = replace_static_path(index.text)
    table_html = fix_sort_table(html_content)
    if table_html is not None:
        html_content = table_html
    new_links = get_links(html_content)
    index_file.write(html_content)
    index_file.close()
    parsed_pages.append({"file": index_html_path, "puncover_url": '/'})
    print("Generating HTML pages")

    for link in new_links:
        process_link(link)
    for plink in pending_links:
        process_link(plink)
        
    print("Updating link references")
    for info in parsed_pages:
        html_content = open(info["file"], "r").read()
        puncover_links = get_links(html_content)
        file_path = str(info["file"])
        if info["puncover_url"] == '/':
            html_content = html_content.replace("../static", "static")
        for link in puncover_links:
            html_local_ref = get_local_html(link[:-1])
            if html_local_ref is None:
                continue
            html_local_ref = str(html_local_ref.name)
            if info["puncover_url"] == '/all':
                html_local_ref = "path/" + html_local_ref
            if info["file"] == index_html_path:
                if html_local_ref != "all.html":
                    html_local_ref = "path/" + html_local_ref
            old_href = 'href="'+link+'"'
            new_href = 'href="'+html_local_ref+'"'
            html_content = html_content.replace(old_href, new_href)
        new_html = open(info["file"], "w+")
        new_html.write(html_content)


local_html()
