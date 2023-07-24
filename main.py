from newletter_gpt.feeds import FeedSource, get_img_url
from newletter_gpt.prompts import gen_summary_and_tags_via_llm
import logging
import mysql.connector
import argparse
from apscheduler.schedulers.blocking import BlockingScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsletterGPT")
logger.setLevel("INFO")

CHATGPT_DEPLOYMENT_NAME = "chatgpt-long"
SLEEP_HOURS = 12


def get_updates(configs, feed_sources):
    with mysql.connector.connect(user=configs.db_user,
                                 password=configs.db_password,
                                 host=configs.db_host,
                                 database=configs.db) as conn, \
            conn.cursor() as cursor:
        cursor.execute("SELECT link from ai_reports")
        links_in_db = cursor.fetchall()
        links_in_db = set(link[0] for link in links_in_db)
        sql_op = "INSERT INTO ai_reports (title, link, publish_time, with_html_noise, content, source, summary, aigc, digital_human, neural_rendering, computer_graphics, computer_vision, robotics, consumer_electronics,img_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"
        logger.info("Try to get updates")
        for feed_name, feed_source in feed_sources.items():
            try:
                logger.info(f"Getting updates from {feed_source.name}")
                feed_items, is_updated, new_items = feed_source.get_feeds()
                if is_updated:
                    for item in new_items:
                        if item.link in links_in_db:
                            continue

                        logger.info(f"Try to generate tags and summary for {item.title}: {item.link}")
                        gen_summary_and_tags_via_llm(item,
                                                     api_base=configs.api_base,
                                                     api_key=configs.api_key,
                                                     chatgpt_deployment_name=CHATGPT_DEPLOYMENT_NAME)
                        tags = item.tags
                        logger.info(f"""Tags for "{item.title}" is {tags}""")
                        relevant = (tags.aigc or tags.computer_vision or tags.computer_graphics
                                    or tags.neural_rendering or tags.digital_human) \
                                   and not (tags.consumer_electronics or tags.robotics)
                        if relevant:
                            img_url = get_img_url(item, configs)
                            feed_data = (item.title, item.link, item.published,
                                         item.with_html_noise, item.content,
                                         item.source, item.summary, item.tags.aigc,
                                         item.tags.digital_human,
                                         item.tags.neural_rendering,
                                         item.tags.computer_graphics,
                                         item.tags.computer_vision,
                                         item.tags.robotics,
                                         item.tags.consumer_electronics, img_url)

                            cursor.execute(sql_op, feed_data)
                            conn.commit()
                            logger.info(f"Added one record:\n"
                                        f"  title: {item.title}\n"
                                        f"  link: {item.link}\n"
                                        f"  published: {item.published}\n"
                                        f"  source: {item.source}\n\n")

            except Exception as e:
                logger.warning(f"exception throws: {e}")
        logger.info(f"Sleep for {SLEEP_HOURS} hours.")


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
    scheduler = BlockingScheduler()
    scheduler.add_job(func=get_updates, args=[args, feed_sources],
                      trigger="interval", seconds=60 * 60 * SLEEP_HOURS)
    logger.info("service started")
    get_updates(args, feed_sources)
    scheduler.start()
