import requests

from bs4 import BeautifulSoup


class IpNotice:
    url = ''

    def __init__(self, url: str):
        self.url = url
        self.countries = []
        self.request_page = requests.get(self.url)

        if self.request_page.status_code == 200:
            self.parser_page = BeautifulSoup(self.request_page.text, 'html.parser')
        else:
            self.parser_page = None

    def __call__(self):
        pass

    def status(self):
        print(f'{self.url}: {self.request_page.status_code}')
