import gc
import logging
import time
import traceback

from django.core.paginator import Paginator
from django.db import transaction


class LoggingMixin(object):
    _disable_logging = False
    _logger = None

    def set_logger(self, logger=None):
        # logger argument should be result of logging.getLogger(name) call
        # todo add isinstance check
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
        # used for id exclusion from success update
        self.error = True