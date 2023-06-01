# NewsletterGPT

Get a newsletter summarized by GPT from multiple RSS sources.

## Getting Started
1. Clone this repo.
2. Install dependencies `pip install -r requirements.txt`.
3. You will need to have an Azure OpenAI Service API key.
    * A OpenAI Key is also fine, but the code now only accepts an Azure OpenAI Service API key for now. PRs are welcome.
4. Run `python main.py` to start the server with the following arguments:
    * `--db-user`: SQL Database username
    * `--db-password`: SQL Database password
    * `--db-host`: SQL Database host address
    * `--db`: SQL Database name
    * `--api-base`: Azure API base
    * `--api-version`: Azure API version
    * `--endpoint`: Azure API endpoint
    * `--api-key`: Azure API key

## TODOs
- [ ] A client that fetches feeds that are stored in the DB

## Useful Source
Find RSS sources:
* Feeddd: https://github.com/feeddd/feeds