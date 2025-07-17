import os
from pathlib import Path
from platformdirs import user_data_dir

if 'DATABASE_CONN_STRING' not in os.environ:
    raise Exception("DATABASE_CONN_STRING environment variable is not set")

DATABASE_CONN_STRING = os.environ['DATABASE_CONN_STRING']
PROJECT_ID = os.environ['PROJECT_ID']
