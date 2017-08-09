import requests
import itertools
from django.test import TestCase, mock
from model_mommy import mommy

from scraper.models import School, Department
from scraper.management.commands.scrape_data import BulkLoader, Url


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.ok = (status_code < 400)

        def json(self):
            return self.json_data

        def raise_for_status(self):
            raise requests.HTTPError

    if args[0] == 'http://t.com/t':
        return MockResponse({'success': True}, 200)
    elif args[0] == 'http://t.com/at':
        return MockResponse({'key2': 'value2'}, 200)
    elif args[0] == 'https://www.myedu.com/adms/school/1/department/':
        json_data = {
            'status': 200,
            'message': 'OK',
            'result': {
                'Department': {
                    24542: {
                        'UID': 24542,
                        'abbreviation': 'AGED',
                        'datasource_code': 'EXP',
                        'datasource_id': 1,
                        'datasource_user_id': 15,
                        'department_id': 24542,
                        'department_course_seo_url': '/TAMU-Texas-A-and-M-University/AGED/department/24542/course/',
                        'department_professor_seo_url': '/TAMU-Texas-A-and-M-University/AGED/department/24542/professor/',
                        'name': None,
                        'school_id': 206,
                        'school_abbrev': 'TAMU',
                        'school_name': 'Texas A&M University'
                    },
                    24543: {
                        'UID': 24543,
                        'abbreviation': 'MSCI',
                        'datasource_code': 'EXP',
                        'datasource_id': 1,
                        'datasource_user_id': 15,
                        'department_id': 24543,
                        'department_course_seo_url': '/TAMU-Texas-A-and-M-University/MSCI-Medical-Sciences/department/24543/course/',
                        'department_professor_seo_url': '/TAMU-Texas-A-and-M-University/MSCI-Medical-Sciences/department/24543/professor/',
                        'name': 'Medical Sciences',
                        'school_id': 206,
                        'school_abbrev': 'TAMU',
                        'school_name': 'Texas A&M University'
                    },
                    24544: {
                        'UID': 24544,
                        'abbreviation': 'METR',
                        'datasource_code': 'EXP',
                        'datasource_id': 1,
                        'datasource_user_id': 15,
                        'department_id': 24544,
                        'department_course_seo_url': '/TAMU-Texas-A-and-M-University/METR-Meteorology/department/24544/course/',
                        'department_professor_seo_url': '/TAMU-Texas-A-and-M-University/METR-Meteorology/department/24544/professor/',
                        'name': 'Meteorology',
                        'school_id': 206,
                        'school_abbrev': 'TAMU',
                        'school_name': 'Texas A&M University'
                    },
                    24547: {
                        'UID': 24547,
                        'abbreviation': 'ELIC',
                        'datasource_code': 'EXP',
                        'datasource_id': 1,
                        'datasource_user_id': 15,
                        'department_id': 24547,
                        'department_course_seo_url': '/TAMU-Texas-A-and-M-University/ELIC-Composition/department/24547/course/',
                        'department_professor_seo_url': '/TAMU-Texas-A-and-M-University/ELIC-Composition/department/24547/professor/',
                        'name': 'Composition',
                        'school_id': 206,
                        'school_abbrev': 'TAMU',
                        'school_name': 'Texas A&M University'
                    }
                }
            }
        }
        return MockResponse(json_data, 200)
    elif args[0] == 'https://www.myedu.com/adms/school/2/department/':
        return MockResponse({}, 200)
    elif args[0] == 'https://www.myedu.com/adms/school/3/department/':
        raise requests.ConnectionError

    return MockResponse(None, 404)


# Create your tests here.
class BulkLoaderTest(TestCase):
    # todo rewrite using setupclass method or setuptestdata
    def setUp(self):
        mommy.make(School, school_id=1)
        mommy.make(School, school_id=2)
        mommy.make(School, school_id=3)
        dep_lists = []
        for sc in School.objects.all():
            dep_lists.append(mommy.prepare(Department, _quantity=3, school_id=sc.school_id, school_name=sc.school_name))
        self.prepared_deps = itertools.chain(*dep_lists)
        self.tbl = BulkLoader()

    def tearDown(self):
        School.objects.all().delete()
        Department.objects.all().delete()
        self.prepared_deps = []
        # todo think about testability while refactoring
        # this is needed cause I have to update this class attributes for proper testing
        BulkLoader.save_list = []
        BulkLoader.success_ids = []
        self.tbl = None

    def test_get_urls(self):
        urls = list(self.tbl.get_urls())
        self.assertEqual(len(urls), School.objects.count())
        for url in urls:
            self.assertIsInstance(url, Url)
            self.assertEqual(url.url, self.tbl.url_template.format(url.id_to_update))
            self.assertTrue(School.objects.filter(school_id=url.id_to_update, department_scraped=False).exists())

        tsch = School.objects.first()
        tsch.department_scraped = True
        tsch.save()
        urls = list(self.tbl.get_urls())
        self.assertEqual(len(urls), School.objects.filter(department_scraped=False).count())

        School.objects.update(department_scraped=True)
        urls = list(self.tbl.get_urls())
        self.assertEqual(len(urls), 0)

    # todo test get_response and various exceptions
    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_get_response(self, mock_get):
        result = self.tbl.get_response('http://t.com/t')
        self.assertTrue(result['success'])
        self.assertRaises(requests.HTTPError, lambda: self.tbl.get_response('http://t.com/404'))

    def test_get_objects_from_url(self):
        self.tbl.key = 'result'
        success_data = {'success': True}
        data = {'result': success_data}
        result = self.tbl.get_objects_from_url(data)
        self.assertEqual(result, success_data)
        self.tbl.key = 'result.test'
        data = {'result': {'test': success_data}}
        result = self.tbl.get_objects_from_url(data)
        self.assertEqual(result, success_data)
        self.tbl.key = 'result.not_exist'
        self.assertDictEqual(self.tbl.get_objects_from_url(data), {})

    def test_update_db(self):
        self.tbl.success_ids = School.objects.values_list('school_id', flat=True)
        self.tbl.save_list = self.prepared_deps
        self.assertFalse(School.objects.filter(department_scraped=True).exists())
        self.assertEqual(Department.objects.count(), 0)
        self.tbl.update_db()
        self.assertFalse(School.objects.filter(department_scraped=False).exists())
        self.assertEqual(Department.objects.count(), School.objects.count() * 3)
        self.assertFalse(self.tbl.work_with_db)
        self.assertFalse(self.tbl.success_ids)
        self.assertFalse(self.tbl.save_list)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_process_url_success(self, mock_get):
        sc_success = School.objects.get(school_id=1)
        url = Url(self.tbl.url_template.format(sc_success.school_id), sc_success.id)
        self.assertFalse(self.tbl.save_list)
        self.assertFalse(self.tbl.success_ids)
        self.tbl.process_url(url=url)
        self.assertEqual(len(self.tbl.save_list), 4)
        self.assertEqual(len(self.tbl.success_ids), 1)
        self.assertIn(1, self.tbl.success_ids)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_process_url_empty(self, mock_get):
        sc_empty = School.objects.get(school_id=2)
        url = Url(self.tbl.url_template.format(sc_empty.school_id), sc_empty.id)
        self.assertFalse(self.tbl.save_list)
        self.assertFalse(self.tbl.success_ids)
        self.tbl.process_url(url=url)
        self.assertFalse(self.tbl.save_list)
        self.assertEqual(len(self.tbl.success_ids), 1)
        self.assertIn(2, self.tbl.success_ids)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_process_url_connection_error(self, mock_get):
        sc_error = School.objects.get(school_id=3)
        url = Url(self.tbl.url_template.format(sc_error.school_id), sc_error.id)
        self.assertFalse(self.tbl.save_list)
        self.assertFalse(self.tbl.success_ids)
        self.tbl.process_url(url=url)
        self.assertFalse(self.tbl.save_list)
        self.assertFalse(self.tbl.success_ids)
        self.assertNotIn(3, self.tbl.success_ids)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_process_urls(self, mock_get):
        self.assertFalse(School.objects.filter(department_scraped=True).exists())
        self.assertEqual(Department.objects.count(), 0)
        self.tbl.process_urls()
        self.assertEqual(School.objects.filter(department_scraped=False).count(), 1)
        sc_error = School.objects.get(department_scraped=False)
        self.assertEqual(sc_error.school_id, 3)
        self.assertEqual(School.objects.filter(department_scraped=True).count(), 2)
        self.assertEqual(Department.objects.count(), 4)
        self.assertFalse(self.tbl.work_with_db)
        self.assertFalse(self.tbl.success_ids)
        self.assertFalse(self.tbl.save_list)
