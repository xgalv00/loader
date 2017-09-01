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
        # todo think about set_logger as Descriptor
        # class attribute logger as Descriptor with logger name
        self.set_logger(logger=logger)
        self.saver.set_logger(logger=logger)
        self.fetcher.set_logger(logger=logger)

    def log_configuration(self):
        self.log('Loader: {}'.format(self))
        self.log('Fetcher: {}'.format(self.fetcher))
        self.log('Saver: {}'.format(self.saver))

    # max_req_count max number of requests that should be emmited
    def load(self, max_req_count=10):

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
    # multiplier for queue size
    concurrent_multiplier = 3

    def __init__(self, fetcher_cls, saver_cls, concurrent=5, logger=None, config=None):
        super().__init__(fetcher_cls, saver_cls, config=config, logger=logger)
        self.concurrent = concurrent
        self.fq = Queue(maxsize=(self.concurrent * self.concurrent_multiplier))
        self.sq = Queue()

    def fetch_worker(self):
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
        while True:
            item = self.sq.get()
            self.saver.append(fetched_url=item)
            self.sq.task_done()

    def create_workers(self):
        for i in range(self.concurrent):
            t = Thread(target=self.fetch_worker)
            t.daemon = True
            t.start()

        st = Thread(target=self.save_worker, daemon=True)
        st.start()

    def load(self, max_req_count=10):

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


class CoroutineLoader(Loader):

    def get_fetched_object(self):
        while True:
            url = yield
            furl = self.fetcher.fetch(url=url)
            if furl.error:
                self.error_count += 1
            else:
                self.saver.append(fetched_url=furl)

    async def coroutine(self, url):
        furl = self.fetcher.fetch(url=url)
        return furl

    def load(self, max_req_count=10):

        self.log('Start data loading')
        self.log_configuration()

        event_loop = asyncio.get_event_loop()
        urls = islice(self.fetcher.get_urls(), max_req_count)
        try:
            f = asyncio.wait([event_loop.run_in_executor(None, self.fetcher.fetch, url) for url in urls])
            result = event_loop.run_until_complete(f)
        finally:
            event_loop.close()
        done_tasks = result[0]
        for dt in done_tasks:
            furl = dt.result()
            if furl.error:
                self.error_count += 1
            else:
                self.saver.append(fetched_url=furl)
            self.req_count += 1

        # final db update
        self.saver.update_db()

        self.log('Requests issued {}. Errors {}'.format(self.req_count, self.error_count))
        self.log('Finish data loading')
