import os

os.environ.setdefault('PROJECT_ID', 'test')
os.environ.setdefault('DATABASE_CONN_STRING', 'sqlite+libsql:///:memory:')
os.environ.setdefault('LIBSQL_SYNC_URL', '')
os.environ.setdefault('LIBSQL_AUTH_TOKEN', '')
