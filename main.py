from newletter_gpt.feeds import FeedSource
from newletter_gpt.prompts import gen_summary_and_tags_via_llm
import random
import time
import logging
import mysql.connector
import argparse
import guidance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsletterGPT")
logger.setLevel("INFO")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetcher of feeds")
    parser.add_argument("--db-user", type=str)
    parser.add_argument("--db-password", type=str)
    parser.add_argument("--db-host", type=str)
    parser.add_argument("--db", type=str)
    parser.add_argument("--api-base", type=str)
    parser.add_argument("--api-version", type=str)
    parser.add_argument("--endpoint", type=str)
    parser.add_argument("--api-key", type=str)
    args = parser.parse_args()

    guidance.llm = guidance.llms.OpenAI(model="text-davinci-003",
                                        api_base=args.api_base,
                                        api_type="azure",
                                        api_version=args.api_version,
                                        endpoint=args.endpoint,
                                        api_key=args.api_key)

    feed_sources = {
        "机器之心": FeedSource("机器之心", "https://www.jiqizhixin.com/rss"),
        "量子位": FeedSource("量子位", "https://www.qbitai.com/rss"),
        "新智元": FeedSource("新智元", "https://feed.hamibot.com/api/feeds/61aa18e9486e3727fb090ba1"),
    }

    with mysql.connector.connect(user=args.db_user,
                                 password=args.db_password,
                                 host=args.db_host,
                                 database=args.db) as conn, \
            conn.cursor() as cursor:
        sql_op = "INSERT INTO ai_reports (title, link, publish_time, with_html_noise, content, source, summary, aigc, digital_human, neural_rendering, computer_graphics, computer_vision, robotics, consumer_electronics) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        logger.info("Enter loop")
        while True:
            for feed_name, feed_source in feed_sources.items():

                feed_items, is_updated, new_items = feed_source.get_feeds()
                if is_updated:
                    # save relevant feeds
                    feed_data = []
                    for item in new_items:
                        try:
                            logger.info(f"Try to generate tags and summary for {item.title}: {item.link}")
                            gen_summary_and_tags_via_llm(item)
                            tags = item.tags
                            relevant = (tags.aigc or tags.computer_vision or tags.computer_graphics
                                        or tags.neural_rendering or tags.digital_human) \
                                       and not (tags.consumer_electronics or tags.robotics)
                            if relevant:
                                feed_data.append((item.title, item.link, item.published, item.with_html_noise,
                                                  item.content, item.source, item.summary,
                                                  item.tags.aigc, item.tags.digital_human, item.tags.neural_rendering,
                                                  item.tags.computer_graphics, item.tags.computer_vision,
                                                  item.tags.robotics, item.tags.consumer_electronics))
                                logger.info(f"Try to add one record:\n"
                                            f"  title: {item.title}\n"
                                            f"  link: {item.link}\n"
                                            f"  published: {item.published}\n"
                                            f"  source: {item.source}\n\n")
                        except Exception as e:
                            logger.warning(f"exception throws: {e}")

                    try:
                        if len(feed_data) > 0:
                            cursor.executemany(sql_op, feed_data)
                            conn.commit()
                    except Exception as e:
                        logger.warning(f"exception throws: {e}")

            # sleep for a random time between 12 and 24 hours
            sleep_time = random.randint(12, 24) * 60 * 60
            logger.info(f"Sleeping for {sleep_time / (60 * 60)} hours and then check new update.")
            time.sleep(sleep_time)
