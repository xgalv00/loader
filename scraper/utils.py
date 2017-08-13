import gc
import logging
import time
from queue import Queue
from threading import Thread

import requests
from django.core.paginator import Paginator
from django.db import transaction

from scraper.models import School, Department


class LoggingMixin(object):
    _disable_logging = False
    _logger = None

    def set_logger(self, logger=None):
        # logger argument should be result of logging.getLogger(name) call
        if logger:
            self._logger = logger
        else:
            # Logger was not provided. Continue without logging
            self._disable_logging = True

    def log(self, msg, level=logging.INFO, exc_info=False):
        # todo get caller info (class, function, thread or process)
        # todo use self.stdout.write or print if logger is not available
        if self._logger and not self._disable_logging:
            self._logger.log(level, msg, exc_info=exc_info)

# todo remove this after refactoring
# placed here due to circular importing
from scraper.datagetters import API_URL, SCHOOL_PATH, DEPARTMENT_PATH, Url


class ProcessBigAmountsMixin(LoggingMixin):
    chunksize = 1000
    chunktimeout = 0
    model = None

    def get_queryset(self):
        return self.model.objects.all()

    def queryset_iterator(self, queryset):
        count = queryset.count()
        self.log('Process ({})'.format(count))
        if not count > 0:
            self.log('0 objects processed')
            raise StopIteration

        start_index = 1
        # eliminate problem for queryset laziness when changing queryset's filter criteria in object
        # example
        # from school.models import School
        # School.objects.filter(is_saved=False).count()
        # if you update flag is_saved for every chunk queryset will be halved
        # understand better queryset laziness trying to optimize this
        # and look here for reference https://stackoverflow.com/questions/10548744/django-lazy-queryset-and-pagination
        ids = list(queryset.values_list('id', flat=True))
        paginator = Paginator(ids, self.chunksize)
        # paginator = Paginator(queryset, self.chunksize)
        page = paginator.page(1)
        has_next_chunk = True
        while has_next_chunk:
            obj_instances = queryset.model.objects.filter(id__in=page.object_list)
            # obj_instances = page.object_list
            with transaction.atomic():
                for index, row in enumerate(obj_instances, start_index):
                    yield row

            start_index = index + 1
            gc.collect()
            if page.has_next():
                self.log('{} processed from {}'.format(self.chunksize * page.number, count))
                page = paginator.page(page.next_page_number())
                time.sleep(self.chunktimeout)
            else:
                has_next_chunk = False


# todo divide BulkLoader to Executor, DataGetter and DataSaver classes
class BulkLoader(LoggingMixin):
    url_template = '{api_url}{obj_path}'.format(api_url=API_URL, obj_path=DEPARTMENT_PATH)
    # string for traversing json objects
    key = 'result.Department'
    req_count = 0
    max_req_count = 300
    save_count = 100
    success_ids = []
    save_list = []
    save_class = Department
    fetch_class = School
    work_with_db = False
    _error = False

    # todo add logger argument which could be string or actual logger
    def __init__(self, logger=None):
        super(BulkLoader, self).__init__()
        self.set_logger(logger=logger)

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
        return self.fetch_class.objects.filter(department_scraped=False).values_list('school_id', flat=True)

    def get_urls(self):
        values_queryset = self.get_values_queryset()
        for v in values_queryset:
            query_url = self.url_template.format(v)
            # todo move this id propagation to a dict where url will be the key and propagated id one of the values
            yield Url(query_url, id_to_update=v)

    def process_url(self, url):
        """Expects Url instance to process"""

        self._error = False
        # todo use try except else instead of _error = True
        # todo move this to process_url method
        try:
            resp_data = self.get_response(url.url)
        except (KeyboardInterrupt, SystemExit):
            self.log('Going to halt now', level=logging.WARNING)
            # http://effbot.org/zone/stupid-exceptions-keyboardinterrupt.html
            raise
        # maybe add division by requests exceptions (Timeout, HTTPError, ConnectionError)
        except requests.RequestException:
            # todo add handle_error method
            # todo check error reporting when disconnected
            self.log('Request exception: {}'.format(url.url), level=logging.ERROR)
            self._error = True
            objs = {}
        except:
            # todo propagate exc_info=True
            # https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
            self.log('Unexpected error: {}'.format(url.url), level=logging.ERROR)
            # print("Unexpected error:", sys.exc_info()[0])
            self._error = True
            objs = {}
        else:
            objs = self.get_objects_from_url(resp_data)

        # todo move to save_objs method after refactoring and decoupling
        for key in objs.keys():
            obj = objs[key]
            # todo think better name for url
            obj.update({'source_url': url.url})
            # add sleep here. Should wait with list population while updating db
            #  or maybe this is not a problem
            # Should i use queues instead of lists?
            # add subtle logging to check if this is a problem especially in thread mode
            # todo rewrite with conditional variables or events and make all alive threads wait until work with db is not complete
            while self.work_with_db:
                time.sleep(1)
            # todo think if save_list could be a bunch of url objects not actual class to save,
            #  so I can remove success_ids list
            self.save_list.append(self.save_class(**obj))
            # add to success dict for bulk update via method final_update
            # if url.id_to_update:
            #     self.success_ids.append(url.id_to_update)

        # url without objects in result list should be marked as processed
        if not self._error:
            while self.work_with_db:
                time.sleep(1)
            # add to success dict for bulk update via method final_update
            if url.id_to_update:
                self.success_ids.append(url.id_to_update)

    def process_urls(self):
        self.log('Start data loading')
        for url in self.get_urls():

            self.process_url(url)

            if self.req_count % self.save_count == 0:
                self.update_db()
                self.log('Process request {}'.format(self.req_count))

            self.req_count += 1

            if self.req_count == self.max_req_count:
                self.log('Hit max request at {}'.format(self.req_count))
                break
        self.update_db()
        self.log('Finish data loading')

    def update_db(self):
        # todo add transaction here and halt execution in case of any problems
        # understand could be a problem here when adding new values to this lists while db queries
        # try switch to use queue
        # https://stackoverflow.com/questions/6319207/are-lists-thread-safe
        self.work_with_db = True
        School.objects.filter(school_id__in=self.success_ids).update(department_scraped=True)
        self.save_class.objects.bulk_create(objs=self.save_list)
        self.save_list = []
        self.success_ids = []
        self.work_with_db = False


class ThreadedBulkLoader(BulkLoader):
    # todo add as argument to initialization of class
    concurrent = 5
    # multiplier for queue size
    _concurrent_multiplier = 3
    max_req_count = 15000

    def __init__(self, logger=None):
        super(ThreadedBulkLoader, self).__init__(logger=logger)
        self.q = Queue(self.concurrent * self._concurrent_multiplier)

    def process_urls(self):

        def worker():
            while True:
                item = self.q.get()
                # todo make process url method to add processed url to another queue that will be consumed by single process or thread
                self.process_url(item)
                self.q.task_done()
                # todo add acquire lock here
                self.req_count += 1

        for i in range(self.concurrent):
            t = Thread(target=worker)
            t.daemon = True
            t.start()

        self.log('Start data loading')
        for url in self.get_urls():
            self.q.put(url)

            # todo think where this counters should be
            if self.req_count > 0 and self.req_count % self.save_count == 0:
                self.update_db()
                self.log('Process request {}'.format(self.req_count))

            if self.req_count == self.max_req_count:
                self.log('Hit max request at {}'.format(self.req_count))
                break
        self.q.join()
        # if this is before join some small amount of objects wasn't saved
        self.update_db()
        self.log('Finish data loading')


class PaginatedBulkLoader(BulkLoader):
    key = 'result.School'
    url_template = '{api_url}{obj_path}'.format(api_url=API_URL, obj_path=SCHOOL_PATH)
    save_class = School
    pages = 1
    max_req_count = 2000
    save_count = 100

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
                yield Url('{url}?page={page}'.format(url=query_url, page=page))
                page += 1
        else:
            yield Url(query_url)

    def process_urls(self):
        self.log('Start data loading')
        for url in self.get_urls():

            self.process_url(url)

            if self.req_count > 0 and self.req_count % self.save_count == 0:
                self.update_db()
                self.log('Process request {}'.format(self.req_count))

            self.req_count += 1

            if self.req_count == self.max_req_count:
                self.log('Hit max request at {}'.format(self.req_count))
                break
        self.update_db()
        self.log('Finish data loading')
