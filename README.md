# NewsletterGPT

Get a newsletter summarized by GPT from multiple RSS sources.

## Getting Started

1. Clone this repo.
2. Install dependencies `pip install -r requirements.txt`.
3. You will need to have an Azure OpenAI Service API key.
    * A OpenAI Key is also fine, but the code now only accepts an Azure OpenAI Service API key for now. PRs are welcome.
    * Set `CHATGPT_DEPLOYMENT_NAME` and `COMPLETION_DEPLOYMENT_NAME` in `main.py`
4. Run `python main.py` to start the server with the following arguments:
    * `--db-user`: SQL Database username
    * `--db-password`: SQL Database password
    * `--db-host`: SQL Database host address
    * `--db`: SQL Database name
    * `--api-base`: Azure API base
    * `--api-key`: Azure API key
    * `--access_key_id`: Access key ID to OSS server
    * `--access_key_secret`: Access key to OSS server
    * `--bucket_name`: Bucket name in OSS server
    * `--endpoint`: Endpoint to OSS server

## TODOs

- [ ] A client that fetches feeds that are stored in the DB

## Useful Source

Find RSS sources:

* Feeddd: https://github.com/feeddd/feeds