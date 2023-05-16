from newletter_gpt.feeds import FeedSource
from datetime import datetime, timedelta
import random
import time


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
