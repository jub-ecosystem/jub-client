from dotenv import load_dotenv
import os
import string

ENV_FILE_PATH = os.environ.get("ENV_FILE_PATH", ".env")
if os.path.exists(ENV_FILE_PATH):
    load_dotenv(ENV_FILE_PATH)


JUB_CLIENT_LOG_PATH                = os.environ.get("JUB_CLIENT_LOG_PATH", "/log")
JUB_CLIENT_OBSERVATORY_ID_SIZE     = int(os.environ.get("JUB_CLIENT_OBSERVATORY_ID_SIZE","12"))
JUB_CLIENT_OBSERVATORY_ID_ALPHABET = string.ascii_lowercase+string.digits