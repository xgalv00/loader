from scraper.datagetters import DataGetter, PaginatedDataGetter
from scraper.datasavers import DataSaver
from scraper.utils import LoggingMixin
from scraper.models import School, Department


class Executor(LoggingMixin):

    getter = DataGetter(fetch_class=School)
    saver = DataSaver(save_count=100, save_class=Department)

    def __init__(self, max_req_count=100):
        super().__init__()
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

        self.log('Finish data loading. Requests issued {}. Errors {}'.format(self.req_count, self.error_count))


# todo remove this class after switch to @classmethod usage
class PaginatedExecutor(Executor):
    getter = PaginatedDataGetter()
    saver = DataSaver(save_count=100, save_class=School)
