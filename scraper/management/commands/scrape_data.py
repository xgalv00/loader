import logging

from django.core.management.base import BaseCommand

from scraper.loaders import ThreadedLoader, AsyncLoader, Loader
from scraper.fetchers import DepartmentFetcher, CourseFetcher, ProfessorFetcher
from scraper.savers import DepartmentSaver, CourseSaver, ProfessorSaver


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--reqs',
            type=int,
            help='Set maximum request for each loader that should be emitted',
        )

    def handle(self, *args, **options):
        logger = logging.getLogger('import')
        # todo create saver for this loader with checking before saving if object is already in db
        # PaginatedExecutor(logger=logger, max_req_count=2000).execute()
        # common_kwargs = {'config': {'fetcher': {'url_class': AiohttpUrl}, 'saver': {'save_count': 100}}, 'logger': logger}
        common_kwargs = {'config': {'saver': {'save_count': 100}}, 'logger': logger}
        # dep_loader = ThreadedLoader(fetcher_cls=DepartmentFetcher, saver_cls=DepartmentSaver, **common_kwargs)
        # course_loader = ThreadedLoader(fetcher_cls=CourseFetcher, saver_cls=CourseSaver, **common_kwargs)
        # prof_loader = ThreadedLoader(fetcher_cls=ProfessorFetcher, saver_cls=ProfessorSaver, **common_kwargs)
        # reqs = 500
        # dep_loader.load(max_req_count=reqs)
        # course_loader.load(max_req_count=reqs)
        # prof_loader.load(max_req_count=reqs)
        # course_loader = ThreadedLoader(fetcher_cls=CourseFetcher, saver_cls=CourseSaver, **common_kwargs)
        # course_loader = Loader(fetcher_cls=CourseFetcher, saver_cls=CourseSaver, **common_kwargs)
        course_loader = AsyncLoader(fetcher_cls=CourseFetcher, saver_cls=CourseSaver, **common_kwargs)
        reqs = 100
        course_loader.load(max_req_count=reqs)
