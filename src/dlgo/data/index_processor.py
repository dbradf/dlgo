from concurrent.futures import ThreadPoolExecutor as Executor
import os

import click
import requests

KGS_URL = 'http://u-go.net/gamerecords/'
INDEX_PAGE = 'kgs_index.html'
DATA_DIRECTORY = 'data'


def get_and_write(url, filename):

    print(f'Downloading {filename}...')
    response = requests.get(url)
    with open(filename, 'w') as fileh:
        fileh.write(response.text)
    print(f'Download {filename} complete.')


class KGSIndex(object):
    def __init__(self, url: str = KGS_URL, index: str = INDEX_PAGE, target_dir: str = DATA_DIRECTORY):
        self.url = url
        self.index_page = index
        self.target_dir = target_dir
        self.urls = []
        self.file_info = []

    def download_files(self):
        if not os.path.isdir(self.target_dir):
            os.makedirs(self.target_dir)

        jobs = []
        with Executor() as exe:
            for file_info in self.file_info:
                url = file_info['url']
                file_name = os.path.join(self.target_dir, file_info['filename'])
                jobs.append(exe.submit(get_and_write, url, file_name))

        for j in jobs:
            j.result()

    def create_index_page(self):
        """If there is no local html containing links to files, create one."""
        if os.path.isfile(self.index_page):
            print('>>> Reading cached index page')
            with open(self.index_page, 'r') as index_file:
                index_contents = index_file.read()
        else:
            print('>>> Downloading index page')
            response = requests.get(self.url)
            response.raise_for_status()
            index_contents = response.text

            with open(self.index_page, 'w') as index_file:
                index_file.write(index_contents)
        return index_contents

    def load_index(self):
        index_contents = self.create_index_page()
        split_page = [item for item in index_contents.split('<a href="') if
                      item.startswith("https://")]

        for item in split_page:
            download_url = item.split('">Download')[0]
            if download_url.endswith('.tar.gz'):
                self.urls.append(download_url)

        for url in self.urls:
            filename = os.path.basename(url)
            split_file_name = filename.split('-')
            num_games = int(split_file_name[len(split_file_name) - 2])
            print(f"{filename} {num_games}")
            self.file_info.append({'url': url, 'filename': filename, 'num_games': num_games})


@click.command()
def main():
    index = KGSIndex()
    index.load_index()
    index.download_files()
