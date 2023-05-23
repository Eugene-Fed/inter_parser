import requests
import json
import time
import re
import itertools
import bs_interface as parser

from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

YELLOW_PAGES_URL = r'https://www.interpol.int/How-we-work/Notices/View-Red-Notices'
RED_PAGES_URL = r'https://www.interpol.int/How-we-work/Notices/View-Yellow-Notices'

bs4_pages = {
    'red': parser.IpNotice(url=RED_PAGES_URL),
    'yellow': parser.IpNotice(url=YELLOW_PAGES_URL)
}


for page in bs4_pages.values():
    page.status()
