import logging

from django.core.management.base import BaseCommand

from scraper.utils import PaginatedBulkLoader, ThreadedBulkLoader


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--reqs',
            type=int,
            help='Set maximum request that should be emitted',
        )

    def handle(self, *args, **options):
        logger = logging.getLogger('import')
        PaginatedBulkLoader(logger=logger).process_urls()
        ThreadedBulkLoader(logger=logger).process_urls()
