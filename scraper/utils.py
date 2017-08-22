import gc
import logging
import time
import traceback

import requests

from django.core.paginator import Paginator
from django.db import transaction


class LoggingMixin(object):
    disable_logging = False
    logger = None

    def set_logger(self, logger=None):
        # logger argument should be result of logging.getLogger(name) call
        if isinstance(logger, logging.Logger):
            self.logger = logger
        else:
            # correct logger was not provided. Continue without logging
            self.disable_logging = True

    def log(self, msg, level=logging.INFO, exc_info=False):
        if self.logger and not self.disable_logging:
            self.logger.log(level, msg, exc_info=exc_info)

    def get_class_name(self):
        return self.__class__.__name__


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


class Url(object):
    """helper class used to store all necessary data about urls that should be processed"""

    def __init__(self, url, id_to_update=None):
        self.url_string = url
        self.id_to_update = id_to_update
        self.fetched_dicts = []
        self.error = False

    def get_response(self):
        response = requests.get(self.url_string, timeout=10)
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()

    def append_fetched_dicts(self, objs):
        for key in objs.keys():
            obj = objs[key]
            obj.update({'source_url': self.url_string})
            self.fetched_dicts.append(obj)

    # arguments are sys.exc_info() unpacked
    def handle_error(self, logger, exc_type, exc_value, exc_traceback):
        last_tb_line = traceback.format_exc().splitlines()[-1]
        # exc_info could be set to True, but last tb line printing is enough for now
        if logger is not None:
            logger.log(msg='Url: {}, e_val: {}'.format(self.url_string, last_tb_line), level=logging.ERROR)
        # used for id exclusion from success update
        self.error = True
