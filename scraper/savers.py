from abc import ABCMeta, abstractmethod

from django.db import transaction

from scraper.models import School, Department, Course, Professor
from scraper.utils import LoggingMixin


class AbstractSaver(LoggingMixin, metaclass=ABCMeta):

    save_class = None

    def __init__(self, save_count=1):
        super().__init__()
        self.save_count = save_count
        self.success_ids = []
        self.save_list = []
        self.work_with_db = False
        self.not_saved_count = 0

    @abstractmethod
    def update_fetched_objects(self):
        pass

    def __repr__(self, *args, **kwargs):
        return '{}(save_count={!r})'.format(self.get_class_name(), self.save_count)

    def update_db(self):
        # understand could be a problem here when adding new values to this lists while db queries
        # try switch to use queue
        # https://stackoverflow.com/questions/6319207/are-lists-thread-safe
        # todo add if save_class is None print saved object to log file as info level
        self.work_with_db = True
        with transaction.atomic():
            self.update_fetched_objects()
            self.save_class.objects.bulk_create(objs=self.save_list)
        self.save_list = []
        self.success_ids = []
        self.work_with_db = False

    def append(self, fetched_url):
        # errors in fetched urls should be handled by executors not savers
        for obj in fetched_url.fetched_dicts:
            self.save_list.append(self.save_class(**obj))
        self.success_ids.append(fetched_url.id_to_update)
        self.not_saved_count += 1
        if self.not_saved_count > 0 and self.not_saved_count % self.save_count == 0:
            count_to_save = len(self.save_list)
            self.update_db()
            self.log('Save {} of objects, from {} urls'.format(count_to_save, self.save_count))
            self.not_saved_count = 0

    @classmethod
    def get_saver(cls, config):
        return cls(**config)


class SchoolSaver(AbstractSaver):
    save_class = School

    def update_fetched_objects(self):
        return []


class DepartmentSaver(AbstractSaver):
    save_class = Department

    def update_fetched_objects(self):
        return School.objects.filter(school_id__in=self.success_ids).update(department_scraped=True)


class CourseSaver(AbstractSaver):
    save_class = Course

    def update_fetched_objects(self):
        return Department.objects.filter(department_id__in=self.success_ids).update(course_scraped=True)


class ProfessorSaver(AbstractSaver):
    save_class = Professor

    def update_fetched_objects(self):
        return Department.objects.filter(department_id__in=self.success_ids).update(professor_scraped=True)


