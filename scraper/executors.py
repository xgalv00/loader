from collections import deque
from queue import Queue
from threading import Thread

from scraper.datagetters import DataGetter, PaginatedDataGetter
from scraper.datasavers import DataSaver
from scraper.utils import LoggingMixin
from scraper.models import School, Department


class Executor(LoggingMixin):

    getter = DataGetter(fetch_class=School)
    saver = DataSaver(save_count=100, save_class=Department)

    def __init__(self, max_req_count=10, logger=None):
        super().__init__()
        self.set_logger(logger=logger)
        self.saver.set_logger(logger=logger)
        self.getter.set_logger(logger=logger)
        self.max_req_count = max_req_count
        self.req_count = 0
        self.error_count = 0

    def execute(self):

        self.log('Start data loading')
        for url in self.getter.get_urls():
            furl = self.getter.fetch_url(url=url)
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


# todo remove this class after switch to @classmethod usage
class PaginatedExecutor(Executor):
    getter = PaginatedDataGetter()
    saver = DataSaver(save_count=100, save_class=School)


class ThreadedExecutor(Executor):
    # multiplier for queue size
    _concurrent_multiplier = 3

    def __init__(self, max_req_count=100, concurrent=5, logger=None):
        super().__init__(max_req_count=max_req_count, logger=logger)
        self.concurrent = concurrent
        self.q = Queue(maxsize=(self.concurrent * self._concurrent_multiplier))

    def execute(self):

        def worker():
            while True:
                item = self.q.get()
                # todo make fetch_url method to add fetched url to another queue that will be consumed by single process or thread
                furl = self.getter.fetch_url(url=item)
                if furl.error:
                    self.error_count += 1
                else:
                    self.saver.append(fetched_url=furl)
                # todo add acquire lock here
                self.req_count += 1
                self.q.task_done()

        for i in range(self.concurrent):
            t = Thread(target=worker)
            t.daemon = True
            t.start()

        self.log('Start data loading')
        for url in self.getter.get_urls():
            self.q.put(url)
            # this might be not accurate, cause urls put in queue still be processed even if loop stops,
            #  think how to fix this
            if self.req_count == self.max_req_count:
                self.log('Hit max request at {}'.format(self.req_count))
                break

        self.q.join()
        # final db update
        self.saver.update_db()

        self.log('Requests issued {}. Errors {}'.format(self.req_count, self.error_count))
        self.log('Finish data loading')
