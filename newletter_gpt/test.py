import argparse
from feeds import test


parser = argparse.ArgumentParser(description="oss connecter")
parser.add_argument("--access_key_id", type=str)
parser.add_argument("--access_key_secret", type=str)
parser.add_argument("--bucket_name", type=str)
parser.add_argument("--endpoint", type=str)
args = parser.parse_args()
test(args)
