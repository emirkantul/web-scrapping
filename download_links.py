import os, sys, glob, re
import json
from pprint import pprint
import time

import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import uuid

from config import LINK_LIST_PATH

# Encoding for writing the URLs to the .txt file
# Do not change unless you are getting a UnicodeEncodeError
ENCODING = "utf-8"


def save_link(url, page):
    """
    Save collected link/url and page to the .txt file in LINK_LIST_PATH
    """
    id_str = uuid.uuid3(uuid.NAMESPACE_URL, url).hex
    with open(LINK_LIST_PATH, "a", encoding=ENCODING) as f:
        f.write("\t".join([id_str, url, str(page)]) + "\n")


def download_links_from_index():
    """
    This function should go to the defined "url" and download the news page links from all
    pages and save them into a .txt file.
    """

    # Checking if the link_list.txt file exists
    if not os.path.exists(LINK_LIST_PATH):
        with open(LINK_LIST_PATH, "w", encoding=ENCODING) as f:
            f.write("\t".join(["id", "url", "page"]) + "\n")
        start_page = 1
        downloaded_url_list = []

    # If some links have already been downloaded,
    # get the downloaded links and start page
    else:
        # Get the page to start from
        data = pd.read_csv(LINK_LIST_PATH, sep="\t")
        if data.shape[0] == 0:
            start_page = 1
            downloaded_url_list = []
        else:
            start_page = data["page"].astype("int").max()
            downloaded_url_list = data["url"].to_list()

    base_url = "https://mfa.gov.sc/news"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "http://www.google.com/",
    }

    for page in range(start_page, 201):  # Iterate through pages 1 to 200
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}/page/{page}"

        response = requests.get(url, headers=headers)
        time.sleep(3)

        soup = bs(response.content, "html.parser")
        blog_content = soup.find("div", {"id": "blog_content"})

        if blog_content is None:
            print(f"Error: Could not find blog content on page {page}")
            continue

        posts = blog_content.find_all("div", class_="single-postblog")
        for post in posts:
            read_more_link = post.find("div", class_="rmb").find("a")
            collected_url = read_more_link["href"]

            if collected_url not in downloaded_url_list:
                print("\t", collected_url, flush=True)
                save_link(collected_url, page)


if __name__ == "__main__":
    download_links_from_index()
