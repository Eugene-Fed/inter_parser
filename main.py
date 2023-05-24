import requests
import json
import time
import re
import itertools

from bs_interface import IpNotice
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

YELLOW_PAGES_URL = r'https://www.interpol.int/How-we-work/Notices/View-Red-Notices'
RED_PAGES_URL = r'https://www.interpol.int/How-we-work/Notices/View-Yellow-Notices'

bs4_pages = {
    'red': IpNotice(url=RED_PAGES_URL),
    'yellow': IpNotice(url=YELLOW_PAGES_URL)
}


for key, value in bs4_pages.items():
    print(f'Page `{key}` get_status: {value.get_status()}')
    print(value())
