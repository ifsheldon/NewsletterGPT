from newletter_gpt.feeds import FeedSource
from newletter_gpt.prompts import gen_summary_via_llm, get_tags_via_llm
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

    feed_sources = {
        "机器之心": FeedSource("机器之心", "https://www.jiqizhixin.com/rss"),
        "量子位": FeedSource("量子位", "https://www.qbitai.com/rss"),
        "新智元": FeedSource("新智元", "https://feed.hamibot.com/api/feeds/61aa18e9486e3727fb090ba1"),
    }
    last_update_time = datetime.now()
    start_time = datetime.fromisoformat("Mon, 15 May 2023 08:00:00 +0800")
    one_week = timedelta(days=7)
    week_end = start_time + one_week
    feeds_this_week = set()

    while True:
        for feed_name, feed_source in feed_sources.items():
            feed_items, is_updated, new_items = feed_source.get_feeds()
            if is_updated:
                print(f"New entries from {feed_name}:")
                for item in new_items:
                    print(f"{item.title}: {item.link}")
                    feeds_this_week.add(item)

        if datetime.now() > week_end:
            print("Sending newsletter")
            print(f"Feeds this week: {feeds_this_week}")
            feeds_this_week = set()
            week_end = datetime.now() + one_week
        # sleep for a random time between 12 and 24 hours
        sleep_time = random.randint(12, 24) * 60 * 60
        print(f"Sleeping for {sleep_time} seconds")
        time.sleep(sleep_time)
