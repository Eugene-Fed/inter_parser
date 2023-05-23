import requests
import json
import time
import re
import itertools

from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

YELLOW_PAGES_URL = r'https://www.interpol.int/How-we-work/Notices/View-Red-Notices'
RED_PAGES_URL = r'https://www.interpol.int/How-we-work/Notices/View-Yellow-Notices'

notices = {
    'yellow_pages': requests.get(YELLOW_PAGES_URL),
    'red_pages': requests.get(RED_PAGES_URL)
}

for key, value in notices.items():
    print(key, value.status_code)
