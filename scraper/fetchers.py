import sys
from abc import ABCMeta, abstractmethod

import requests

from scraper.utils import LoggingMixin, Url

API_URL = 'https://www.myedu.com/adms'
SCHOOL_PATH = '/school/'
DEPARTMENT_PATH = '/school/{}/department/'
COURSE_PATH = '/department/{department_id}/course/'
PROFESSOR_PATH = '/department/{department_id}/professor/'


class AbstractUrlFetcher(LoggingMixin, metaclass=ABCMeta):
    # string to format url for fetch
    url_template = ''
    # string for traversing json objects
    key = ''
    url_class = Url

    @abstractmethod
    def fetch(self, url):
        pass

    @classmethod
    def get_fetcher(cls, config):
        return cls(**config)


class BaseFetcher(AbstractUrlFetcher):
    url_template = '{api_url}{obj_path}'.format(api_url=API_URL, obj_path=DEPARTMENT_PATH)
    key = 'result.Department'

    # class to get_urls from get_values_queryset should be redefined
    # if None than get_urls should know how to get urls for processing

    def __init__(self, fetch_class=None):
        super().__init__()
        self.fetch_class = fetch_class

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
            yield self.url_class(query_url, id_to_update=v)

    def fetch(self, url):
        try:
            # todo move get_response to Url class
            # todo think where to handle exceptions while requests.get
            #  maybe define your own exception and raise it from this exceptions
            resp_data = self.get_response(url.url)
        # maybe add division by requests exceptions (Timeout, HTTPError, ConnectionError)
        except requests.RequestException as e:
            url.handle_error(self._logger, *sys.exc_info())
            objs = {}
        except Exception as e:
            url.handle_error(self._logger, *sys.exc_info())
            objs = {}
        else:
            objs = self.get_objects_from_url(resp_data)

        url.append_fetched_dicts(objs=objs)

        return url


class PaginatedFetcher(BaseFetcher):
    key = 'result.School'
    url_template = '{api_url}{obj_path}'.format(api_url=API_URL, obj_path=SCHOOL_PATH)

    def __init__(self, fetch_class=None):
        super().__init__(fetch_class)
        self.pages = 1

    def is_paginated(self, url):
        paged_url = '{url}{query}'.format(url=url, query='?page=1')
        # todo add logging and error handling here
        resp_result = self.get_response(paged_url)
        try:
            pag_dict = resp_result['pagination']
        except KeyError:
            return False
        else:
            self.pages = pag_dict['pages']
            return True

    def get_urls(self):
        query_url = self.url_template
        if self.is_paginated(query_url):
            page = 1
            while page <= self.pages:
                yield self.url_class('{url}?page={page}'.format(url=query_url, page=page))
                page += 1
        else:
            yield self.url_class(query_url)
