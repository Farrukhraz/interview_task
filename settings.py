import configparser

from pathlib import Path


config = configparser.ConfigParser()
config_file_path = Path(__file__).absolute().parent.joinpath('config.ini')
with open(config_file_path, encoding='utf-8') as f:
    config.readfp(f)


DB_NAME = config["postgres"]["DBName"]
DB_USERNAME = config["postgres"]["Username"]
DB_PASSWORD = config["postgres"]["Password"]
DB_HOST = config["postgres"]["Host"]
DB_PORT = config["postgres"]["Port"]
