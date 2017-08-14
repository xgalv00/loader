from scraper.datagetters import DataGetter
from scraper.datasavers import DataSaver
from scraper.utils import LoggingMixin, Department


class Executor(LoggingMixin):

    getter = DataGetter(max_req_count=100)
    saver = DataSaver(save_count=100, save_class=Department)

    def execute(self):
        self.log('Start data loading')

        for furl in self.getter.fetch_urls():
            self.saver.append(fetched_url=furl)
        self.saver.finish_loading()

        self.log('Finish data loading')
