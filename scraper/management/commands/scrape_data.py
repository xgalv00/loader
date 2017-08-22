import logging

from django.core.management.base import BaseCommand

from scraper.loaders import ThreadedLoader
from scraper.fetchers import DepartmentFetcher, CourseFetcher, ProfessorFetcher
from scraper.savers import DepartmentSaver, CourseSaver, ProfessorSaver


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--reqs',
            type=int,
            help='Set maximum request that should be emitted',
        )

    def handle(self, *args, **options):
        logger = logging.getLogger('import')
        # todo create saver for this loader with checking before saving if object is already in db
        # PaginatedExecutor(logger=logger, max_req_count=2000).execute()
        # todo move this to load method
        common_kwargs = {'config': {'saver': {'save_count': 100}}, 'logger': logger, 'max_req_count': 2000}
        dep_loader = ThreadedLoader(fetcher_cls=DepartmentFetcher, saver_cls=DepartmentSaver, **common_kwargs)
        course_loader = ThreadedLoader(fetcher_cls=CourseFetcher, saver_cls=CourseSaver, **common_kwargs)
        prof_loader = ThreadedLoader(fetcher_cls=ProfessorFetcher, saver_cls=ProfessorSaver, **common_kwargs)

        dep_loader.load()
        course_loader.load()
        prof_loader.load()
