from collections import deque
from queue import Queue
from threading import Thread, Lock
from abc import ABCMeta, abstractmethod

from scraper.utils import LoggingMixin


class AbstractLoader(LoggingMixin, metaclass=ABCMeta):

    @abstractmethod
    def load(self):
        pass


class Loader(AbstractLoader):

    # max_req_count max number of requests that should be emmited
    def __init__(self, fetcher_cls, saver_cls, max_req_count=10, logger=None, config=None):
        super().__init__()
        if config is None:
            config = {}
        # todo add logging of fetcher and saver instances
        self.saver = saver_cls.get_saver(config.get('saver', {}))
        self.fetcher = fetcher_cls.get_fetcher(config.get('fetcher', {}))
        # todo think about set_logger as Descriptor
        # class attribute logger as Descriptor with logger name
        self.set_logger(logger=logger)
        self.saver.set_logger(logger=logger)
        self.fetcher.set_logger(logger=logger)
        self.max_req_count = max_req_count
        self.req_count = 0
        self.error_count = 0

    def load(self):

        self.log('Start data loading')
        for url in self.fetcher.get_urls():
            furl = self.fetcher.fetch(url=url)
            if furl.error:
                self.error_count += 1
            else:
                self.saver.append(fetched_url=furl)
            self.req_count += 1

            if self.req_count == self.max_req_count:
                self.log('Hit max request at {}'.format(self.req_count))
                break

        # final db update
        self.saver.update_db()

        self.log('Requests issued {}. Errors {}'.format(self.req_count, self.error_count))
        self.log('Finish data loading')


class ThreadedLoader(Loader):
    # multiplier for queue size
    _concurrent_multiplier = 3

    # todo maybe move configuration to class method for better arguments
    def __init__(self, fetcher_cls, saver_cls, max_req_count=100, concurrent=5, logger=None, config=None):
        super().__init__(fetcher_cls, saver_cls, config=config, max_req_count=max_req_count, logger=logger)
        self.concurrent = concurrent
        self.fq = Queue(maxsize=(self.concurrent * self._concurrent_multiplier))
        self.sq = Queue()

    def fetch_worker(self):
        l = Lock()

        while True:
            item = self.fq.get()
            furl = self.fetcher.fetch(url=item)
            # todo test error handling
            if furl.error:
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

    def load(self):

        self.create_workers()

        self.log('Start data loading')
        for url in self.fetcher.get_urls():
            self.fq.put(url)
            # this might be not accurate, cause urls put in queue still be processed even if loop stops,
            #  think how to fix this
            if self.req_count == self.max_req_count:
                self.log('Hit max request at {}'.format(self.req_count))
                break

        self.fq.join()
        self.sq.join()
        # final db update
        self.saver.update_db()

        self.log('Requests issued {}. Errors {}'.format(self.req_count, self.error_count))
        self.log('Finish data loading')
