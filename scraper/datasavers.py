from django.db import transaction

from scraper.models import School, Department
from scraper.utils import LoggingMixin


class DataSaver(LoggingMixin):

    def __init__(self, save_count=100, save_class=None):
        super().__init__()
        self.save_class = save_class
        self.save_count = save_count
        self.success_ids = []
        self.save_list = []
        self.work_with_db = False
        self.not_saved_count = 0

    def update_fetched_objects(self):
        School.objects.filter(school_id__in=self.success_ids).update(department_scraped=True)

    def update_db(self):
        # todo add transaction here and halt execution in case of any problems
        # understand could be a problem here when adding new values to this lists while db queries
        # try switch to use queue
        # https://stackoverflow.com/questions/6319207/are-lists-thread-safe
        # todo add if save_class is None print to log file as info level
        self.work_with_db = True
        with transaction.atomic():
            self.update_fetched_objects()
            self.save_class.objects.bulk_create(objs=self.save_list)
        self.save_list = []
        self.success_ids = []
        self.work_with_db = False

    def finish_loading(self):
        self.update_db()

    def append(self, fetched_url):
        for obj in fetched_url.fetched_dicts:
            self.save_list.append(self.save_class(**obj))
        self.not_saved_count += 1
        if self.not_saved_count > 0 and self.not_saved_count % self.save_count == 0:
            self.update_db()
            self.log('Save {} of objects, for {} url'.format(len(self.save_list), self.save_count))
            self.not_saved_count = 0
