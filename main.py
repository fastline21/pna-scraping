import requests
import json
import base64
from bs4 import BeautifulSoup
from datetime import datetime
from insidermanila import InsiderManila
from article import Article
import re
import os
from urllib.parse import urlparse
import urllib
from dotenv import load_dotenv

load_dotenv(verbose=True)

current_date = datetime.now().strftime("%B %e, %Y,")

user = InsiderManila(username=os.getenv("USERNAME"), password=os.getenv("PASSWORD"), url=os.getenv("URL"))

token = base64.b64encode(user.credential().encode())

header = {"Authorization": "Basic " + token.decode("utf-8")}

base_url = "https://www.pna.gov.ph/articles"
url = f"{base_url}/list"
page = requests.get(url)

post_need = int(os.getenv("POST_NEED"))
post_count = 0
post_array = []

soup = BeautifulSoup(page.content, "html.parser")
last_page = soup.find("ul", class_="pagination").find_all("li")[-1].find("a")["href"][17:]

for current_page in range(1, int(last_page)):
    current_url = f"{base_url}/list?p={current_page}"
    page = requests.get(current_url)

    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find(id="content")

    article_items = results.find_all('div', class_="article")

    for article_item in article_items:
        # Link
        link = article_item.find("a")["href"]

        # Parse Site
        article_url = base_url + link[-8:]
        article_page = requests.get(article_url)
        article_soup = BeautifulSoup(article_page.content, "html.parser")

        article_date = article_soup.find("span", class_="date").contents[1]
        if current_date in article_date or post_count < post_need:
            article = Article(title=article_soup.find("div", class_="page-header").find("h1").contents[0],
                              content=article_soup.find("div", class_="page-content").findAll(
                                  "p") if not article_soup.find("div", class_="page-content").findAll("div", {
                                  "dir": "auto"}) else article_soup.find("div", class_="page-content").findAll("div", {
                                  "dir": "auto"}),
                              image=article_soup.find("div", class_="page-content").find("img")[
                                  "src"] if article_soup.find("div", class_="page-content").find(
                                  "img") is not None else None)

            # Increment Post Count
            post_count += 1

            # Article Image
            if article.image is not None:
                image = urllib.request.urlopen(article.image.replace(" ", "%20"))
                url_parse = urllib.request.urlopen(article.image.replace(" ", "%20"))
                extension = os.path.splitext(os.path.basename(urlparse(article.image.replace(" ", "%20")).path))[1]
                output = open(
                    "images/" + str(post_count).zfill(len(str(post_need))) + ". " + re.sub('[^A-Za-z0-9]+', ' ',
                                                                                           article.title) + extension,
                    "wb")
                output.write(image.read())
                output.close()

            # Post Body
            post = {
                "date": str(datetime.now()),
                "title": article.title,
                "content": ''.join(str(i) for i in article.content),
                "categories": "32",
                "status": "publish"
            }

            # Posting in WordPress API
            r = requests.post(user.url + "/posts", headers=header, json=post)

            # Data
            json_data = {
                "title": article.title,
                "link": r.json()["link"]
            }

            # Generate JSON File
            if post_count == 1:
                with open("data.json", "w") as new_json:
                    json.dump([json_data], new_json)
            else:
                with open("data.json", "r+") as old_json:
                    data = json.load(old_json)
                    data.append(json_data)
                    old_json.seek(0)
                    json.dump(data, old_json)

            # Post Count Output
            print(post_count)
        else:
            exit()
