# Copyright 2022, Victor Chavez (chavez-bermudez@fh-aachen.de)
# SPDX-License-Identifier: GPL-3.0-or-later
import requests
import pathlib
import re
import os
import argparse
import shutil 

version = "1.1.0"

url_base = "http://127.0.0.1:5000/"

parser = argparse.ArgumentParser(
    prog='Puncover offline HTML',
    description='Builds offline html for puncover',
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

def add_footer(old_html):
    footer_find = '<div id="page-footer">'
    footer_start = old_html.find(footer_find)
    puncover_html_footer = """\n<p  style="color:#808080">Offline html copy built by 
			      <a href="https://github.com/vChavezB/puncover_html" target="_blank">Puncover HTML</a>VERSION</p>\n
			   """
    puncover_html_footer = puncover_html_footer.replace("VERSION"," v"+version)
    footer_end_str = "</div>"
    footer_end = footer_start + old_html[footer_start:].find(footer_end_str)
    new_html = old_html[:footer_end] + puncover_html_footer + old_html[footer_end:]
    return new_html

def fix_jquery(old_html):
    script_find = "<script"
    include_jquery_str = '<script src="/static/js/jquery-3.6.1.min.js"></script>\n'
    script_start = old_html.find(script_find)
    new_html = old_html[:script_start] + include_jquery_str + old_html[script_start:]
    return new_html

def add_table_class(old_html):
    class_table_search = 'class="table'
    table_def_idx = old_html.find(class_table_search)
    if table_def_idx == -1:
        return None
    new_html = old_html[:table_def_idx] \
               + 'class="table js-sort-table' \
               + old_html[table_def_idx + len(class_table_search):]
    return new_html

def fix_sort_table(old_html):
    new_html = add_table_class(old_html)
    if new_html is None:
        return None
    thead_start = new_html.find("<thead>")
    thead_end = new_html.find("</thead>")
    tfoot_start = new_html.find("<tfoot>")
    if tfoot_start == -1:
        return None

    stack_col = new_html.find("Stack</a>") != -1
    code_col = new_html.find("Code</a>") != -1
    static_col = new_html.find("Static</a>") != -1

    thead_simple = """<thead><tr>
                        <th width="100%">Name</th>
                        <th>Remarks</th>
		   """
    if stack_col:
        thead_simple+='\n\t\t\t\t<th class=\"js-sort-number\">Stack</th>'
    if code_col:
        thead_simple+='\n\t\t\t\t<th class=\"js-sort-number\">Code</th>'
    if static_col:
        thead_simple+='\n\t\t\t\t<th class=\"js-sort-number\">Static</th>\n'
    thead_simple+='\n\t\t</tr>\n'
    new_html = new_html[:thead_start] + thead_simple + new_html[thead_end:]
    title_start = new_html.find("<title>")
    sort_script = '\n<script src="../static/js/sorttable.js"></script>\n'
    new_html = new_html[:title_start] + sort_script + new_html[title_start:]
    """
    bottom_row_regex = r"<tr>\n +<th.colspan=\"[0-9]\">&sum"
    tr_modification = '<tr class="sortbottom">'
    match_res = re.finditer(bottom_row_regex, new_html, re.MULTILINE)
    if match_res is not None:
        total_bottom_rows = sum(1 for e in match_res)
        for i in range(0, total_bottom_rows):
            regex_res = re.search(bottom_row_regex, new_html)
            tr_start = regex_res.start()
            new_html = new_html[:tr_start] + tr_modification + new_html[tr_start + len("<tr>"):]
    """
    return new_html


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
    html_content = fix_jquery(html_content)
    html_content = add_footer(html_content)
    table_html = fix_sort_table(html_content)
    if table_html is not None:
        html_content = table_html
    # add relative paths
    if "/all/" not in link:
        html_content = html_content.replace('src="/static', 'src="../static')
        html_content = html_content.replace('href="/static', 'href="../static')
        html_content = html_content.replace('href="/"', 'href="../index.html"')
    else:
        html_content = html_content.replace('href="/static', 'href="static')
        html_content = html_content.replace('href="/"', 'href="index.html"')
        html_content = html_content.replace('src="/static', 'src="static')
	# due to fix_sort_table already adding .. to static
        html_content = html_content.replace('src="../static', 'src="static')
    html_file_name = replace_html_encode(link[:-1]) + ".html"
    if html_file_name.startswith("/"):
        html_file_name = html_file_name[1:]

    if html_file_name.startswith("path/"):
        compact_path = html_file_name[len("path/"):].replace("/", "_")
        html_file_name = "path/" + compact_path

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
    pages_dir_out = dir_out.joinpath("path")
    static_dir_out = dir_out.joinpath("static")
    if not os.path.exists(dir_out):
        os.makedirs(dir_out)
    if not os.path.exists(pages_dir_out):
        os.makedirs(pages_dir_out)
    if not os.path.exists(static_dir_out):
        os.makedirs(static_dir_out)
    # Copy html static dir (css,js,etc) to output
    shutil.copytree(script_root.joinpath("static")), static_dir_out)
    index = requests.get(url_base)
    index_html_path = dir_out.joinpath("index.html")
    index_file = open(index_html_path, "w+")
    html_content = add_footer(index.text)
    html_content = fix_jquery(html_content)
    html_content = replace_static_path(html_content)
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
            old_href = 'href="' + link + '"'
            new_href = 'href="' + html_local_ref + '"'
            html_content = html_content.replace(old_href, new_href)
        new_html = open(info["file"], "w+")
        new_html.write(html_content)


local_html()
