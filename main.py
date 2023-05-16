import datetime
import requests
import random
import time
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass
from dateutil.parser import parse as parse_datetime_from_string
import xml.etree.ElementTree as ET
import re
from bs4 import BeautifulSoup
import openai
import json


@dataclass
class Tags:
    aigc: bool
    digital_human: bool
    neural_rendering: bool
    computer_graphics: bool
    computer_vision: bool


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


@dataclass
class FeedItem:
    title: str
    link: str
    published: datetime
    with_html_noise: bool
    content: str
    summary: Optional[str] = None
    tags: Optional[Tags] = None


def gen_summary_via_llm(feed_item: FeedItem):
    if feed_item.with_html_noise:
        prompt_template = "帮我总结一下这篇文章，这篇文章的题目是{title}：```\n" \
                          "{text}" \
                          "\n```\n" \
                          "文章是从微信公众号获取的，有一些噪音，你可以忽略它们，例如：“参考资料：....”, “预览时标签不可点”, “微信扫一扫关注该公众号”, “编辑：....”和 “轻点两下取消在看”。" \
                          "请先清理噪音，然后再根据清理完的文本来总结。文章总结不要超过300字。结果请严格按照JSON格式返回，格式如下：\n" \
                          "{{ \"cleaned_text\": \"清理完的文本\", \"summary\": \"文章的总结\" }}"
    else:
        prompt_template = "帮我总结一下这篇文章，这篇文章的题目是{title}：```\n" \
                          "{text}" \
                          "\n```\n" \
                          "文章总结不要超过300字。结果请严格按照JSON格式返回，格式如下：\n" \
                          "{{ \"summary\": \"文章的总结\" }}"

    prompt = prompt_template.format(title=feed_item.title, text=feed_item.content)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )
    response_json = json.loads(response.choices[0]["message"]["content"])
    feed_item.summary = response_json["summary"]


def get_tags_via_llm(feed_item: FeedItem):
    prompt_template = "帮我给这篇文章打标签。\n" \
                      "文章标签：```{title}```\n" \
                      "文章内容：```{content}```\n" \
                      "文章总结：```{summary}```\n" \
                      "可用的标签有：\n" \
                      "* aigc: 生成式人工智能相关，例如大语言模型，文生图模型等的相关内容\n" \
                      "* digital_human: 数字人相关，例如数字人，动作捕捉，面部捕捉，数字人形艺术等的相关内容\n" \
                      "* neural_rendering: 神经渲染相关，例如神经渲染器，NeRF，可微分渲染等的相关内容\n" \
                      "* computer_graphics: 计算机图形学相关，例如渲染器，渲染，几何处理，图像处理等的相关内容\n" \
                      "* computer_vision: 计算机视觉相关，例如图像分类，目标检测，图像分割，语义分割，深度估计等的相关内容。注意，脑机接口相关内容不属于计算机视觉的范畴。\n" \
                      "一篇文章可以有多个相关标签，也可以和所有标签都不相关，如果文章和一个标签相关，那么就返回true，否则返回false。" \
                      "请将文章的所有标签严格按照JSON格式返回，一个例子是: " \
                      "{{\"aigc\": true, " \
                      "\"digital_human\": false, " \
                      "\"neural_rendering\": true, " \
                      "\"computer_graphics\": false, " \
                      "\"computer_vision\": false,}}\n"

    prompt = prompt_template.format(title=feed_item.title, content=feed_item.content, summary=feed_item.summary)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )
    response_json = json.loads(response.choices[0]["message"]["content"])
    feed_item.tags = Tags(aigc=response_json["aigc"],
                          digital_human=response_json["digital_human"],
                          neural_rendering=response_json["neural_rendering"],
                          computer_graphics=response_json["computer_graphics"],
                          computer_vision=response_json["computer_vision"])


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


def test():
    feed_sources = {
        "机器之心": FeedSource("机器之心", "https://www.jiqizhixin.com/rss"),
        "量子位": FeedSource("量子位", "https://www.qbitai.com/rss"),
        "新智元": FeedSource("新智元", "https://feed.hamibot.com/api/feeds/61aa18e9486e3727fb090ba1"),
    }
    jiqizhixin = feed_sources["机器之心"]
    feed = jiqizhixin.get_feeds()
    print(feed)
    pass


if __name__ == "__main__":
    test()

    # feed_links = {
    #     "机器之心": "https://www.jiqizhixin.com/rss",
    #     "量子位": "https://www.qbitai.com/rss",
    #     "新智元": "https://feed.hamibot.com/api/feeds/61aa18e9486e3727fb090ba1",
    # }
    # last_update_time = datetime.now()
    # start_time = datetime.fromisoformat("Fri, 8 May 2023 08:00:00 +0800")
    # one_week = timedelta(days=7)
    #
    # while True:
    #     for feed_name, feed_link in feed_links.items():
    #         feed = feedparser.parse(feed_link)
    #         for entry in feed.entries:
    #             if datetime.fromisoformat(entry.published) > last_update_time:
    #                 print(f"New entry: {entry.title}")
    #     # sleep for a random time between 12 and 24 hours
    #     sleep_time = random.randint(12, 24) * 60 * 60
    #     print(f"Sleeping for {sleep_time} seconds")
    #     time.sleep(sleep_time)
    # pass
