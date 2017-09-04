"""
Classes contain fetch logic

All necessary logic is in AbstractUrlFetcher class

Classes PaginatedFetcher, DepartmentFetcher, CourseFetcher, ProfessorFetcher are derived from this abstract class
"""

import sys
from abc import ABCMeta, abstractmethod

from scraper.utils import LoggingMixin, Url
from scraper.models import School, Department

API_URL = 'https://www.myedu.com/adms'
SCHOOL_PATH = '/school/'
DEPARTMENT_PATH = '/school/{}/department/'
COURSE_PATH = '/department/{}/course/'
PROFESSOR_PATH = '/department/{}/professor/'


class AbstractUrlFetcher(LoggingMixin, metaclass=ABCMeta):
    """
    Contains all necessary fetch methods

    get_urls method is abstract and should be implemented by child.

    url_template: string to format url for fetch
    key: string for getting necessary data from response dict
    fetch_class: model class that have all data for url construction and tracking progress
    """

    # string to format url for fetch
    url_template = ''
    # string for traversing json objects
    key = ''
    # if None than get_urls should know how to get urls for processing
    fetch_class = None

    def __init__(self, url_class=Url):
        super().__init__()
        self.url_class = url_class

    def __repr__(self, *args, **kwargs):
        return '{}(url_class={})'.format(self.get_class_name(), self.url_class.__name__)

    def get_objects_from_url(self, data):
        """
        Looks in response dict for objects that should be saved

        Uses self.key to traverse data.
        self.key could contain levels separated by dot.
        If self.key is not found returns empty dict.

        :param data: dict
        :return: dict
        """

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
        """
        Provides variable part of url
        :return: Iterable
        """
        if self.fetch_class is None:
            return []

    @abstractmethod
    def get_urls(self):
        """
        Constructs urls that should be processed
        :return: Iterable
        """
        return self.get_values_queryset()

    async def async_fetch(self, url):
        """
        Makes asynchronous request to url and saves objects to provided instance of url_class

        :param url: Instance of url_class
        :return: Instance of url_class
        """
        try:
            resp_data = await url.get_response()
        except Exception as e:
            url.handle_error(self.logger, *sys.exc_info())
            objs = {}
        else:
            objs = self.get_objects_from_url(resp_data)

        url.append_fetched_dicts(objs=objs)

        return url

    def fetch(self, url):
        """
        Makes request to url and saves objects to provided instance of url_class

        :param url: Instance of url_class
        :return: Instance of url_class
        """
        try:
            #  maybe define your own exception and raise it from this exceptions
            resp_data = url.get_response()
        # maybe add division by requests exceptions (requests.RequestException, Timeout, HTTPError, ConnectionError)
        except Exception as e:
            url.handle_error(self.logger, *sys.exc_info())
            objs = {}
        else:
            objs = self.get_objects_from_url(resp_data)

        url.append_fetched_dicts(objs=objs)

        return url

    @classmethod
    def get_fetcher(cls, config):
        """
        Factory for fetcher construction
        :param config: dict
        :return: fetcher instance initialized from this config
        """
        return cls(**config)


class PaginatedFetcher(AbstractUrlFetcher):
    """Handle urls with pagination"""

    key = 'result.School'
    url_template = '{api_url}{obj_path}'.format(api_url=API_URL, obj_path=SCHOOL_PATH)

    def __init__(self):
        super().__init__()
        self.pages = 1

    def is_paginated(self, url_string):
        """
        Makes preflight requests to provided url and checks if paginated query differs from regular.

        :param url_string: str
        :return: bool
        """

        paged_url = '{url}{query}'.format(url=url_string, query='?page=1')
        url = self.url_class(url=paged_url)
        try:
            resp_result = url.get_response()
        except Exception as e:
            url.handle_error(self.logger, *sys.exc_info())
            raise
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


class DepartmentFetcher(AbstractUrlFetcher):
    url_template = '{api_url}{obj_path}'.format(api_url=API_URL, obj_path=DEPARTMENT_PATH)
    key = 'result.Department'
    fetch_class = School

    def get_values_queryset(self):
        return self.fetch_class.objects.filter(department_scraped=False).values_list('school_id', flat=True)

    def get_urls(self):
        values_queryset = self.get_values_queryset()
        for v in values_queryset:
            query_url = self.url_template.format(v)
            yield self.url_class(query_url, id_to_update=v)


class CourseFetcher(DepartmentFetcher):
    url_template = '{api_url}{obj_path}'.format(api_url=API_URL, obj_path=COURSE_PATH)
    key = 'result.Course'
    fetch_class = Department

    def get_values_queryset(self):
        return self.fetch_class.objects.filter(course_scraped=False).values_list('department_id', flat=True)


class ProfessorFetcher(DepartmentFetcher):
    url_template = '{api_url}{obj_path}'.format(api_url=API_URL, obj_path=PROFESSOR_PATH)
    key = 'result.Professor'
    fetch_class = Department

    def get_values_queryset(self):
        return self.fetch_class.objects.filter(professor_scraped=False).values_list('department_id', flat=True)