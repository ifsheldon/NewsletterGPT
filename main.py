from newletter_gpt.feeds import FeedSource, get_img_url
from newletter_gpt.prompts import gen_summary_and_tags_via_llm
import random
import time
import logging
import mysql.connector
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsletterGPT")
logger.setLevel("INFO")

CHATGPT_DEPLOYMENT_NAME = "chatgpt"
COMPLETION_DEPLOYMENT_NAME = "davinci-completion"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetcher of feeds")
    parser.add_argument("--db-user", type=str, help="username in SQL DB")
    parser.add_argument("--db-password", type=str, help="password for the user in SQL DB")
    parser.add_argument("--db-host", type=str, help="host address of SQL DB")
    parser.add_argument("--db", type=str, help="Schemas name of SQL DB")
    parser.add_argument("--api-base", type=str, help="Azure OpenAI API base")
    parser.add_argument("--api-key", type=str, help="Azure OpenAI API key")
    parser.add_argument("--access_key_id", type=str, help="Access key ID to OSS server")
    parser.add_argument("--access_key_secret", type=str, help="Access key to OSS server")
    parser.add_argument("--bucket_name", type=str, help="Bucket name in OSS server")
    parser.add_argument("--endpoint", type=str, help="Endpoint to OSS server")
    args = parser.parse_args()

    feed_sources = {
        "机器之心":
            FeedSource("机器之心", "https://www.jiqizhixin.com/rss"),
        "量子位":
            FeedSource("量子位", "https://www.qbitai.com/rss"),
    }

    with mysql.connector.connect(user=args.db_user,
                                 password=args.db_password,
                                 host=args.db_host,
                                 database=args.db) as conn, \
            conn.cursor() as cursor:
        cursor.execute("SELECT link from ai_reports")
        links_in_db = cursor.fetchall()
        links_in_db = set(link[0] for link in links_in_db)
        sql_op = "INSERT INTO ai_reports (title, link, publish_time, with_html_noise, content, source, summary, aigc, digital_human, neural_rendering, computer_graphics, computer_vision, robotics, consumer_electronics, img_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"
        logger.info("Enter loop")
        while True:
            for feed_name, feed_source in feed_sources.items():
                try:
                    logger.info(f"Getting updates from {feed_source.name}")
                    feed_items, is_updated, new_items = feed_source.get_feeds()
                    if is_updated:
                        # save relevant feeds
                        feed_data = []
                        for item in new_items:
                            if item.link in links_in_db:
                                continue

                            logger.info(f"Try to generate tags and summary for {item.title}: {item.link}")
                            gen_summary_and_tags_via_llm(item,
                                                         api_base=args.api_base,
                                                         api_key=args.api_key,
                                                         chatgpt_deployment_name=CHATGPT_DEPLOYMENT_NAME,
                                                         completion_deployment_name=COMPLETION_DEPLOYMENT_NAME)
                            tags = item.tags
                            relevant = (tags.aigc or tags.computer_vision or tags.computer_graphics
                                        or tags.neural_rendering or tags.digital_human) \
                                       and not (tags.consumer_electronics or tags.robotics)
                            if relevant:
                                img_url = get_img_url(item, args)
                                feed_data.append(
                                    (item.title, item.link, item.published,
                                     item.with_html_noise, item.content,
                                     item.source, item.summary, item.tags.aigc,
                                     item.tags.digital_human,
                                     item.tags.neural_rendering,
                                     item.tags.computer_graphics,
                                     item.tags.computer_vision,
                                     item.tags.robotics,
                                     item.tags.consumer_electronics, img_url))
                                logger.info(f"Try to add one record:\n"
                                            f"  title: {item.title}\n"
                                            f"  link: {item.link}\n"
                                            f"  published: {item.published}\n"
                                            f"  source: {item.source}\n\n")

                        if len(feed_data) > 0:
                            cursor.executemany(sql_op, feed_data)
                            conn.commit()

                except Exception as e:
                    logger.warning(f"exception throws: {e}")

            # sleep for a random time between 12 and 24 hours
            sleep_time = random.randint(12, 24) * 60 * 60
            logger.info(
                f"Sleeping for {sleep_time / (60 * 60)} hours and then check new update."
            )
            time.sleep(sleep_time)
