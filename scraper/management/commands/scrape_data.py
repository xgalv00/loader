import logging

from django.core.management.base import BaseCommand

from scraper.loaders import PaginatedLoader, ThreadedLoader


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
        ThreadedLoader(logger=logger, max_req_count=20000).execute()
