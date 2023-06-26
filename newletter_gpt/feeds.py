from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_datetime_from_string
import re
import json
import easyocr
import oss2
import os
from requests_html import HTMLSession
import argparse

@dataclass
class Tags:
    aigc: bool
    digital_human: bool
    neural_rendering: bool
    computer_graphics: bool
    computer_vision: bool
    robotics: bool
    consumer_electronics: bool

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


@dataclass
class FeedItem:
    title: str
    link: str
    published: datetime
    with_html_noise: bool
    content: str
    source: str
    summary: Optional[str] = None
    tags: Optional[Tags] = None

    def __eq__(self, other):
        if isinstance(other, FeedItem):
            return self.link == other.link
        else:
            return False

    def __hash__(self):
        return hash(self.link)

    def to_json(self, feed_source: Optional[str] = None) -> str:
        """
        Parse the feed item into a JSON string. Need to use gen_summary_via_llm() first, to ensure that we have a summary.
        :param feed_source: the source of the feed
        :return: JSON string
        """
        assert self.summary is not None, "Get summary first and then parse it into JSON"
        data_dict = {
            "title": self.title,
            "link": self.link,
            "publishTime": self.published.strftime('%Y-%m-%d'),
            "summary": self.summary,
            "tags": None if self.tags is None else self.tags.to_json(),
        }
        if feed_source is not None:
            data_dict["source"] = feed_source
        return json.dumps(data_dict, ensure_ascii=False)


class FeedSource:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.last_update_time: Optional[datetime] = None

    def get_feeds(self) -> (List[FeedItem], bool, List[FeedItem]):
        """
        Get the feeds from the source. If the source is updated, return the new feeds.
        :return: all feeds, whether the source is updated, new feeds
        """
        feed_items = parse_rss(self.url, self.name)
        latest_update_time = max(feed_items, key=lambda x: x.published).published
        if self.last_update_time is None:
            self.last_update_time = latest_update_time
            return feed_items, True, feed_items
        else:
            if latest_update_time > self.last_update_time:
                new_items = list(filter(lambda x: x.published > self.last_update_time, feed_items))
                self.last_update_time = latest_update_time
                return feed_items, True, new_items
            else:
                return feed_items, False, []


def parse_rss(url: str, source: str) -> List[FeedItem]:
    """
    Parse the RSS feed from the url.
    :param url: URL to RSS feed
    :param source: the name of the source
    :return: feed items
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    root = list(root)[0]
    channel_items = list(root)
    raw_feed_items = list(filter(lambda x: x.tag == "item", channel_items))
    feed_items = []
    for feed_item in raw_feed_items:
        title = feed_item.find("title").text
        link = feed_item.find("link").text
        published = feed_item.find("pubDate").text
        content = feed_item.find("content:encoded",
                                 namespaces={"content": "http://purl.org/rss/1.0/modules/content/"})
        if content is None:
            # if there is no content tag, then we need to parse the html content
            html_content = requests.get(link).text
            soup = BeautifulSoup(html_content, "html.parser")
            content = soup.get_text()
            with_html_noise = True
        else:
            # remove all html tags
            content = re.sub("<.*?>", '', content.text)
            with_html_noise = False

        content = re.sub(r"&\w+;", "", content)

        feed_items.append(FeedItem(title=title,
                                   link=link,
                                   published=parse_datetime_from_string(published),
                                   with_html_noise=with_html_noise,
                                   content=content,
                                   source=source))
    return feed_items


def get_img_url(item):
    if item.source == "量子位":
        img_url = liangZiWei(item.link)
    elif item.source == "机器之心":
        img_url = jiQi(item.link)
    elif item.source == "新智元":
        img_url = xinZhiYuan(item.link)
    else:
        img_url = 'None'
    return img_url

#get the image url of the article from liangZiWei
def liangZiWei(web_url):
    urls=[]
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    }

    f = requests.get(web_url, headers=headers).text
    s = BeautifulSoup(f,'lxml')
    s_imgs = s.find_all('img')
    for s_img in s_imgs:
        if "http" not in s_img['src']:
            img_url = 'https://www.qbitai.com' + s_img['src']
            urls.append(img_url)

    if len(urls)<2:
        url ="None"
    else:
        url = urls[1]
    return url

#get the image url of the article from jiQiZhiXin
def jiQi(web_url):
    urls=[]
    f = requests.get(web_url).text
    s = BeautifulSoup(f,'lxml')
    s_imgs = s.find_all('img',attrs = {'logo' : False})
    for s_img in s_imgs:
        if "editor" in s_img['src']:
            img_url = s_img['src']
            urls.append(img_url)
    if urls==[]:
        url = "None "
    else:
        url = urls[0]
    return url

#get the image url of the article from xinZhiYuan
def xinZhiYuan(web_url,args): 
    session = HTMLSession()
    r = session.get(web_url)
    r.html.render() 
    s_imgs = r.html.find('img')

    urls=[]
    for s_img in s_imgs:
        if 'data-src' in s_img.attrs:
            img_url = s_img.attrs['data-src'] 
            urls.append(img_url)
    if len(urls)<1:
        url ="None"
        return url
    
    url = urls[0]
    html = requests.get(url)

    #create a temporary file
    name = web_url[27:]+'.jpg'
    with open(name, 'wb') as file:
        file.write(html.content)

    reader = easyocr.Reader(['ch_sim','en']) 
    result = reader.readtext(name)
    if len(result)>1:
        if len(result[1])>1:
            if result[0][1] =='此图片来自微信公众平台':
                url = "None"
                return url

    # upload and delete the temporary file
    auth = oss2.Auth(args.access_key_id, args.access_key_secret)
    bucket = oss2.Bucket(auth, args.endpoint, args.bucket_name)
    object_key = name
    local_file = name
    bucket.put_object_from_file(object_key, local_file)
    url = (f"https://{args.bucket_name}.{args.endpoint}/{name}")
    os.remove(name)

    return url
