import asyncio

from itertools import islice
from queue import Queue
from threading import Thread, Lock
from abc import ABCMeta, abstractmethod

from scraper.utils import LoggingMixin


class AbstractLoader(LoggingMixin, metaclass=ABCMeta):

    @abstractmethod
    def load(self):
        pass


class Loader(AbstractLoader):
    """
    Contains all necessary load methods

    load method is simple implementation of non concurrent loading.
    """

    def __init__(self, fetcher_cls, saver_cls, logger=None, config=None):
        super().__init__()

        if config is None:
            config = {}

        self.saver = saver_cls.get_saver(config.get('saver', {}))
        self.fetcher = fetcher_cls.get_fetcher(config.get('fetcher', {}))
        self.configure_logging(logger)
        self.req_count = 0
        self.error_count = 0

    def __repr__(self, *args, **kwargs):
        return '{}(fetcher_cls={}, saver_cls={})'.format(self.get_class_name(), self.fetcher.get_class_name(), self.saver.get_class_name())

    def configure_logging(self, logger):
        """
        Propagates given logger to saver and fetcher

        :param logger: logger instance
        """
        self.set_logger(logger=logger)
        self.saver.set_logger(logger=logger)
        self.fetcher.set_logger(logger=logger)

    def log_configuration(self):
        """
        Dumps loader configuration
        """
        self.log('Loader: {}'.format(self))
        self.log('Fetcher: {}'.format(self.fetcher))
        self.log('Saver: {}'.format(self.saver))

    def load(self, max_req_count=10):
        """
        Fetches objects from urls provided by fetcher class
        Saves fetched objects using saver class
        :param max_req_count: int number of requests that should be emmited
        """

        self.log('Start data loading')
        self.log_configuration()
        for url in self.fetcher.get_urls():
            furl = self.fetcher.fetch(url=url)
            if furl.error:
                self.error_count += 1
            else:
                self.saver.append(fetched_url=furl)
            self.req_count += 1

            if self.req_count == max_req_count:
                self.log('Hit max request at {}'.format(self.req_count))
                break

        # final db update
        self.saver.update_db()

        self.log('Requests issued {}. Errors {}'.format(self.req_count, self.error_count))
        self.log('Finish data loading')


class ThreadedLoader(Loader):
    """
    Processes urls using threading module
    """
    # multiplier for queue size
    concurrent_multiplier = 3

    def __init__(self, fetcher_cls, saver_cls, concurrent=5, logger=None, config=None):
        super().__init__(fetcher_cls, saver_cls, config=config, logger=logger)
        self.concurrent = concurrent
        self.fq = Queue(maxsize=(self.concurrent * self.concurrent_multiplier))
        self.sq = Queue()

    def fetch_worker(self):
        """
        Fetches objects from urls provided by fetcher class and puts them to save queue
        """
        l = Lock()

        while True:
            item = self.fq.get()
            furl = self.fetcher.fetch(url=item)
            if furl.error:
                with l:
                    self.error_count += 1
            else:
                self.sq.put(furl)

            with l:
                self.req_count += 1
            self.fq.task_done()

    def save_worker(self):
        """
        Saves fetched objects using saver class
        """
        while True:
            item = self.sq.get()
            self.saver.append(fetched_url=item)
            self.sq.task_done()

    def create_workers(self):
        """
        Creates necessary workers
        """
        for i in range(self.concurrent):
            t = Thread(target=self.fetch_worker)
            t.daemon = True
            t.start()

        st = Thread(target=self.save_worker, daemon=True)
        st.start()

    def load(self, max_req_count=10):
        """
        Creates workers and orchestrates their work
        :param max_req_count: int number of requests that should be emmited
        """

        self.create_workers()

        self.log('Start data loading')
        self.log_configuration()

        urls = islice(self.fetcher.get_urls(), max_req_count)
        for url in urls:
            self.fq.put(url)

        self.fq.join()
        self.sq.join()
        # final db update
        self.saver.update_db()

        self.log('Requests issued {}. Errors {}'.format(self.req_count, self.error_count))
        self.log('Finish data loading')


class AsyncLoader(Loader):
    """
    Processes urls using asyncio module
    """

    # todo replace requests.get call with something async

    def __init__(self, fetcher_cls, saver_cls, connections=10, logger=None, config=None):
        super().__init__(fetcher_cls, saver_cls, logger, config)
        self.loop = asyncio.get_event_loop()
        self.sem = asyncio.Semaphore(connections)

    async def handle_fetched_url(self, futures):
        """
        Propagates fetched url object to saver

        :param futures: futures with urls to fetch through semaphore
        """

        for f in asyncio.as_completed(futures, loop=self.loop):
            furl = await f
            if furl.error:
                self.error_count += 1
            else:
                self.saver.append(fetched_url=furl)
            self.req_count += 1

    async def sem_fetch(self, url):
        """
        Fetch urls using Semaphore

        :param url: url instance
        :return: url instance with fetched_dicts populated
        """
        async with self.sem:
            furl = await self.loop.run_in_executor(None, self.fetcher.fetch, url)
            return furl

    def load(self, max_req_count=10):
        """
        Orchestrates loading process
        :param max_req_count: int number of requests that should be emmited
        """
        self.log('Start data loading')
        self.log_configuration()
        futures = []
        urls = islice(self.fetcher.get_urls(), max_req_count)
        for url in urls:
            future = asyncio.ensure_future(self.sem_fetch(url))
            futures.append(future)
        self.loop.run_until_complete(self.handle_fetched_url(futures))

        # final db update
        self.saver.update_db()

        self.log('Requests issued {}. Errors {}'.format(self.req_count, self.error_count))
        self.log('Finish data loading')
