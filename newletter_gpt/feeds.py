from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_datetime_from_string
import re
import json


@dataclass
class Tags:
    aigc: bool
    digital_human: bool
    neural_rendering: bool
    computer_graphics: bool
    computer_vision: bool


    def to_json(self):
        return json.dumps(self.__dict__, ensure_ascii=False)


@dataclass
class FeedItem:
    title: str
    link: str
    published: datetime
    with_html_noise: bool
    content: str
    summary: Optional[str] = None
    tags: Optional[Tags] = None

    def __eq__(self, other):
        if isinstance(other, FeedItem):
            return self.link == other.link
        else:
            return False

    def __hash__(self):
        return hash(self.link)

    def to_json(self, feed_source: Optional[str]=None):
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
        feed_items = parse_rss(self.url)
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


def parse_rss(url: str):
    response = requests.get(url)
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
            html_content = requests.get(link).text
            soup = BeautifulSoup(html_content, "html.parser")
            content = soup.get_text()
            with_html_noise = True
        else:
            # remove all html tags
            content = re.sub("<.*?>", '', content.text)
            with_html_noise = False

        feed_items.append(FeedItem(title=title,
                                   link=link,
                                   published=parse_datetime_from_string(published),
                                   with_html_noise=with_html_noise,
                                   content=content))
    return feed_items
