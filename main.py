from newletter_gpt.feeds import FeedSource
from newletter_gpt.prompts import gen_summary_via_llm, get_tags_via_llm
from datetime import datetime, timedelta
import random
import time
import logging

logger = logging.getLogger("NewsletterGPT")


if __name__ == "__main__":
    feed_sources = {
        "机器之心": FeedSource("机器之心", "https://www.jiqizhixin.com/rss"),
        "量子位": FeedSource("量子位", "https://www.qbitai.com/rss"),
        "新智元": FeedSource("新智元", "https://feed.hamibot.com/api/feeds/61aa18e9486e3727fb090ba1"),
    }
    # start_time = datetime.fromisoformat("Mon, 15 May 2023 08:00:00 +0800")
    start_time = datetime.now()
    one_week = timedelta(days=7)
    week_end = start_time + one_week
    feeds_this_week = set()

    while True:
        for feed_name, feed_source in feed_sources.items():
            feed_items, is_updated, new_items = feed_source.get_feeds()
            if is_updated:
                # save relevant feeds
                for item in new_items:
                    gen_summary_via_llm(item)
                    get_tags_via_llm(item)
                    if item.is_relevant():
                        logger.info(f" New entries from {feed_name} --  {item.title}: {item.link}")
                        feeds_this_week.add(item)

        # if one week has passed, print related feeds of last week
        if datetime.now() > week_end:
            logger.info(f"Feeds this week: {[feed.to_json() for feed in feeds_this_week]}")
            feeds_this_week = set()
            week_end = datetime.now() + one_week

        # sleep for a random time between 12 and 24 hours
        sleep_time = random.randint(12, 24) * 60 * 60
        logger.info(f"Sleeping for {sleep_time / (60*60)} hours and then check new update.")
        time.sleep(sleep_time)
