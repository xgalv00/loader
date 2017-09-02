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
        return '{}()'.format(self.get_class_name())

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

    @abstractmethod
    def get_urls(self):
        return self.get_values_queryset()

    def fetch(self, url):
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
        return cls(**config)


class PaginatedFetcher(AbstractUrlFetcher):
    key = 'result.School'
    url_template = '{api_url}{obj_path}'.format(api_url=API_URL, obj_path=SCHOOL_PATH)

    def __init__(self):
        super().__init__()
        self.pages = 1

    def is_paginated(self, url_string):
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