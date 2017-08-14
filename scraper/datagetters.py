import logging
import sys
import traceback

import requests

from scraper.utils import LoggingMixin

API_URL = 'https://www.myedu.com/adms'
SCHOOL_PATH = '/school/'
DEPARTMENT_PATH = '/school/{}/department/'
COURSE_PATH = '/department/{department_id}/course/'
PROFESSOR_PATH = '/department/{department_id}/professor/'


class DataGetter(LoggingMixin):
    url_template = '{api_url}{obj_path}'.format(api_url=API_URL, obj_path=DEPARTMENT_PATH)
    # string for traversing json objects
    key = 'result.Department'
    req_count = 0
    max_req_count = 0
    # class to get_urls from get_values_queryset should be redefined
    # if None than get_urls should know how to get urls for processing
    fetch_class = None

    # max_req_count max number of requests that should be emmited
    def __init__(self, max_req_count=100):
        super().__init__()
        self.max_req_count = max_req_count

    @staticmethod
    def get_response(url):
        response = requests.get(url, timeout=10)
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()

    def get_objects_from_url(self, data):
        """Uses self.key to traverse json result"""
        for ki in self.key.split('.'):
            try:
                data = data[ki]
            # TypeError for handling empty list in result
            except (KeyError, TypeError) as e:
                result = {}
            else:
                result = data
        return result

    def get_values_queryset(self):
        if self.fetch_class is None:
            return []
        return self.fetch_class.objects.filter(department_scraped=False).values_list('school_id', flat=True)

    def get_urls(self):
        values_queryset = self.get_values_queryset()
        for v in values_queryset:
            query_url = self.url_template.format(v)
            yield Url(query_url, id_to_update=v)

    def fetch_url(self, url):
        try:
            # todo move get_response to Url class
            # todo think where to handle exceptions while requests.get
            #  maybe define your own exception and raise it from this exceptions
            resp_data = self.get_response(url.url)
        # maybe add division by requests exceptions (Timeout, HTTPError, ConnectionError)
        except requests.RequestException as e:
            url.handle_error(*sys.exc_info())
            objs = {}
        except Exception as e:
            url.handle_error(*sys.exc_info())
            objs = {}
        else:
            objs = self.get_objects_from_url(resp_data)

        url.append_fetched_dicts(objs=objs)

        return url

    def fetch_urls(self):
        for url in self.get_urls():
            yield self.fetch_url(url=url)
            self.req_count += 1

            if self.req_count == self.max_req_count:
                self.log('Hit max request at {}'.format(self.req_count))
                raise StopIteration


# todo make Url class injectable
class Url(LoggingMixin):
    """helper class used to store all necessary data about urls that should be processed"""

    def __init__(self, url, id_to_update=None):
        self.url = url
        self.id_to_update = id_to_update
        self.fetched_dicts = []
        self.error = False

    def append_fetched_dicts(self, objs):
        for key in objs.keys():
            obj = objs[key]
            # todo think better name for url
            obj.update({'source_url': self.url})
            self.fetched_dicts.append(obj)

    # arguments are sys.exc_info() unpacked
    def handle_error(self, exc_type, exc_value, exc_traceback):
        # todo check error reporting when disconnected
        # todo test logging
        # https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
        # https://stackoverflow.com/a/4992124
        last_tb_line = traceback.format_exc().splitlines()[-1]
        # exc_info could be set to True, but last tb line printing is enough for now
        self.log(msg='Url: {}, e_val: {}'.format(self.url, last_tb_line), level=logging.ERROR)
        self.error = True
