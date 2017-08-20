import requests

from django.test import TestCase, mock
from model_mommy import mommy

from scraper.models import School, Department
from scraper.fetchers import BaseFetcher, PaginatedFetcher
from scraper.savers import BaseSaver
from scraper.loaders import Loader
from scraper.utils import Url

DEPARTMENT_RESPONSE_DICT = {
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

SCHOOL_RESPONSE_DICT = {
    2: {
        'UID': 2,
        'abbreviation': 'UHV ',
        'address': '3007 N. Ben Wilson',
        'active': True,
        'campus_setting': 'City: Small',
        'city': 'Victoria',
        'color': '333571',
        'mascot': 'Jaguars',
        'common_name': 'UH-Victoria',
        'datasource_code': 'EXP',
        'datasource_id': 1,
        'datasource_user_id': 15,
        'edu_time': '4-year',
        'edu_type': 'Public',
        'education_network_member': None,
        'has_grades': True,
        'graduate_population': 1806,
        'launch_group_code': 'AUG',
        'launch_group_id': 4,
        'launch_priority': 593,
        'launch_status_code': 'LIVE',
        'launch_status_id': 6,
        'on_campus_avail': True,
        'no_registration': None,
        'parent_school_id': None,
        'revenue': None,
        'school_bucket': '1',
        'school_id': 2,
        'school_name': 'University of Houston-Victoria',
        'school_seo_title': None,
        'school_seo_url': '/UHV-University-of-Houston-Victoria/school/2',
        'school_seo_description': None,
        'course_by_dept_seo_url': '/UHV-University-of-Houston-Victoria/school/2/course/by-department/',
        'degree_by_college_seo_url': '/UHV-University-of-Houston-Victoria/school/2/degree/by-college/',
        'prof_by_dept_seo_url': '/UHV-University-of-Houston-Victoria/school/2/professor/by-department/',
        'school_type': 'Undergraduate',
        'state': 'TX',
        'undergraduate_population': 2289,
        'zip': '77901',
        'registration_url': None,
        'degree_audit_url': None
    },
    8: {
        'UID': 8,
        'abbreviation': None,
        'address': '100 State Sreet',
        'active': None,
        'campus_setting': 'City: Small',
        'city': 'Framingham',
        'color': '505050',
        'mascot': 'Rams',
        'common_name': None,
        'datasource_code': 'EXP',
        'datasource_id': 1,
        'datasource_user_id': 15,
        'edu_time': '4-year',
        'edu_type': 'Public',
        'education_network_member': None,
        'has_grades': False,
        'graduate_population': 2095,
        'launch_group_code': 'BETA',
        'launch_group_id': 1,
        'launch_priority': 1158,
        'launch_status_code': 'NEW',
        'launch_status_id': 1,
        'on_campus_avail': True,
        'no_registration': None,
        'parent_school_id': None,
        'revenue': None,
        'school_bucket': None,
        'school_id': 8,
        'school_name': 'Framingham State University',
        'school_seo_title': None,
        'school_seo_url': '/Framingham-State-University/school/8',
        'school_seo_description': None,
        'course_by_dept_seo_url': '/Framingham-State-University/school/8/course/by-department/',
        'degree_by_college_seo_url': '/Framingham-State-University/school/8/degree/by-college/',
        'prof_by_dept_seo_url': '/Framingham-State-University/school/8/professor/by-department/',
        'school_type': 'Undergraduate',
        'state': 'MA',
        'undergraduate_population': 3858,
        'zip': '01701-9101',
        'registration_url': None,
        'degree_audit_url': None
    },
    10: {
        'UID': 10,
        'abbreviation': None,
        'address': '200 College Rd',
        'active': None,
        'campus_setting': 'Rural: Fringe',
        'city': 'Gallup',
        'color': '505050',
        'mascot': None,
        'common_name': None,
        'datasource_code': 'EXP',
        'datasource_id': 1,
        'datasource_user_id': 15,
        'edu_time': '2-year',
        'edu_type': 'Public',
        'education_network_member': None,
        'has_grades': False,
        'graduate_population': None,
        'launch_group_code': None,
        'launch_group_id': None,
        'launch_priority': 1940,
        'launch_status_code': 'NEW',
        'launch_status_id': 1,
        'on_campus_avail': None,
        'no_registration': True,
        'parent_school_id': None,
        'revenue': None,
        'school_bucket': None,
        'school_id': 10,
        'school_name': 'University of New Mexico-Gallup Campus',
        'school_seo_title': None,
        'school_seo_url': '/University-of-New-Mexico-Gallup-Campus/school/10',
        'school_seo_description': None,
        'course_by_dept_seo_url': '/University-of-New-Mexico-Gallup-Campus/school/10/course/by-department/',
        'degree_by_college_seo_url': '/University-of-New-Mexico-Gallup-Campus/school/10/degree/by-college/',
        'prof_by_dept_seo_url': '/University-of-New-Mexico-Gallup-Campus/school/10/professor/by-department/',
        'school_type': 'Undergraduate',
        'state': 'NM',
        'undergraduate_population': 3010,
        'zip': '87301-5697',
        'registration_url': None,
        'degree_audit_url': None
    },
    11: {
        'UID': 11,
        'abbreviation': None,
        'address': '6001 Dodge Street ',
        'active': None,
        'campus_setting': 'None',
        'city': 'Omaha',
        'color': '505050',
        'mascot': None,
        'common_name': None,
        'datasource_code': 'EXP',
        'datasource_id': 1,
        'datasource_user_id': 15,
        'edu_time': 'unknown',
        'edu_type': 'unknown',
        'education_network_member': None,
        'has_grades': False,
        'graduate_population': None,
        'launch_group_code': None,
        'launch_group_id': None,
        'launch_priority': 6394,
        'launch_status_code': 'NEW',
        'launch_status_id': 1,
        'on_campus_avail': None,
        'no_registration': None,
        'parent_school_id': None,
        'revenue': None,
        'school_bucket': None,
        'school_id': 11,
        'school_name': 'University of Nebraska, Omaha',
        'school_seo_title': None,
        'school_seo_url': '/University-of-Nebraska-Omaha/school/11',
        'school_seo_description': None,
        'course_by_dept_seo_url': '/University-of-Nebraska-Omaha/school/11/course/by-department/',
        'degree_by_college_seo_url': '/University-of-Nebraska-Omaha/school/11/degree/by-college/',
        'prof_by_dept_seo_url': '/University-of-Nebraska-Omaha/school/11/professor/by-department/',
        'school_type': 'Undergraduate',
        'state': 'NE',
        'undergraduate_population': None,
        'zip': '68182',
        'registration_url': None,
        'degree_audit_url': None
    },
    12: {
        'UID': 12,
        'abbreviation': None,
        'address': '3300 Century Ave N',
        'active': None,
        'campus_setting': 'Suburb: Large',
        'city': 'White Bear Lake',
        'color': '505050',
        'mascot': None,
        'common_name': None,
        'datasource_code': 'EXP',
        'datasource_id': 1,
        'datasource_user_id': 15,
        'edu_time': '2-year',
        'edu_type': 'Public',
        'education_network_member': None,
        'has_grades': False,
        'graduate_population': None,
        'launch_group_code': None,
        'launch_group_id': None,
        'launch_priority': 1013,
        'launch_status_code': 'NEW',
        'launch_status_id': 1,
        'on_campus_avail': None,
        'no_registration': None,
        'parent_school_id': None,
        'revenue': None,
        'school_bucket': None,
        'school_id': 12,
        'school_name': 'Century Community and Technical College',
        'school_seo_title': None,
        'school_seo_url': '/Century-Community-and-Technical-College/school/12',
        'school_seo_description': None,
        'course_by_dept_seo_url': '/Century-Community-and-Technical-College/school/12/course/by-department/',
        'degree_by_college_seo_url': '/Century-Community-and-Technical-College/school/12/degree/by-college/',
        'prof_by_dept_seo_url': '/Century-Community-and-Technical-College/school/12/professor/by-department/',
        'school_type': 'Undergraduate',
        'state': 'MN',
        'undergraduate_population': 10918,
        'zip': '55110',
        'registration_url': None,
        'degree_audit_url': None
    }
}

PAGINATION_DICT = {
    'results': 10,
    'page': 1,
    'pages': 2,
    'per_page': 5
}


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
                'Department': DEPARTMENT_RESPONSE_DICT
            }
        }
        return MockResponse(json_data, 200)
    elif args[0] == 'https://www.myedu.com/adms/school/2/department/':
        return MockResponse({}, 200)
    elif args[0] == 'https://www.myedu.com/adms/school/3/department/':
        raise requests.ConnectionError
    elif args[0] == 'https://www.myedu.com/adms/school/paginated?page=1':
        return MockResponse({
            'status': 200,
            'message': 'OK',
            'result': {},
            'pagination': PAGINATION_DICT
        }, 200)
    elif args[0] == 'https://www.myedu.com/adms/school/notpaginated?page=1':
        return MockResponse({
            'status': 200,
            'message': 'OK',
            'result': {},
        }, 200)
    elif args[0] == 'https://www.myedu.com/adms/school/?page=1' or args[
        0] == 'https://www.myedu.com/adms/school/?page=2':
        return MockResponse({
            'status': 200,
            'message': 'OK',
            'result': {
                'School': SCHOOL_RESPONSE_DICT
            },
            'pagination': PAGINATION_DICT
        }, 200)

    return MockResponse(None, 404)


class DataGetterTest(TestCase):
    def setUp(self):
        mommy.make(School, school_id=1)
        mommy.make(School, school_id=2)
        mommy.make(School, school_id=3)
        self.tdg = BaseFetcher(fetch_class=School)

    def tearDown(self):
        School.objects.all().delete()
        Department.objects.all().delete()
        # todo think about testability while refactoring
        # this is needed cause I have to update this class attributes for proper testing
        del self.tdg

    def test_get_urls(self):
        urls = list(self.tdg.get_urls())
        self.assertEqual(len(urls), School.objects.count())
        for url in urls:
            self.assertIsInstance(url, Url)
            self.assertEqual(url.url, self.tdg.url_template.format(url.id_to_update))
            self.assertTrue(School.objects.filter(school_id=url.id_to_update, department_scraped=False).exists())

        tsch = School.objects.first()
        tsch.department_scraped = True
        tsch.save()
        urls = list(self.tdg.get_urls())
        self.assertEqual(len(urls), School.objects.filter(department_scraped=False).count())

        School.objects.update(department_scraped=True)
        urls = list(self.tdg.get_urls())
        self.assertEqual(len(urls), 0)

    # todo test get_response and various exceptions
    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_get_response(self, mock_get):
        result = self.tdg.get_response('http://t.com/t')
        self.assertTrue(result['success'])
        self.assertRaises(requests.HTTPError, lambda: self.tdg.get_response('http://t.com/404'))

    def test_get_objects_from_url(self):
        self.tdg.key = 'result'
        success_data = {'success': True}
        data = {'result': success_data}
        result = self.tdg.get_objects_from_url(data)
        self.assertEqual(result, success_data)
        self.tdg.key = 'result.test'
        data = {'result': {'test': success_data}}
        result = self.tdg.get_objects_from_url(data)
        self.assertEqual(result, success_data)
        self.tdg.key = 'result.not_exist'
        self.assertDictEqual(self.tdg.get_objects_from_url(data), {})

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_fetch_url_success(self, mock_get):
        sc_success = School.objects.get(school_id=1)
        url = Url(self.tdg.url_template.format(sc_success.school_id), sc_success.id)
        self.assertFalse(url.fetched_dicts)
        self.assertEqual(url.id_to_update, 1)
        self.tdg.fetch(url=url)
        # todo add better testing for actual dict values from response
        self.assertEqual(len(url.fetched_dicts), 4)
        self.assertFalse(url.error)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_fetch_url_empty(self, mock_get):
        sc_empty = School.objects.get(school_id=2)
        url = Url(self.tdg.url_template.format(sc_empty.school_id), sc_empty.id)
        self.assertFalse(url.fetched_dicts)
        self.assertEqual(url.id_to_update, 2)
        self.tdg.fetch(url=url)
        self.assertFalse(url.fetched_dicts)
        self.assertFalse(url.error)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_fetch_url_connection_error(self, mock_get):
        sc_error = School.objects.get(school_id=3)
        url = Url(self.tdg.url_template.format(sc_error.school_id), sc_error.id)
        self.assertFalse(url.fetched_dicts)
        self.assertEqual(url.id_to_update, 3)
        self.tdg.fetch(url=url)
        self.assertFalse(url.fetched_dicts)
        self.assertTrue(url.error)


class DataSaverTest(TestCase):
    def setUp(self):
        mommy.make(School, school_id=2)
        self.furl = Url('test', id_to_update=2)
        self.furl.append_fetched_dicts(objs=DEPARTMENT_RESPONSE_DICT)
        self.tsr = BaseSaver(save_count=10, save_class=Department)

    def tearDown(self):
        School.objects.all().delete()
        del self.tsr
        del self.furl

    def test_update_db(self):
        self.tsr.append(fetched_url=self.furl)
        self.assertFalse(School.objects.filter(department_scraped=True).exists())
        self.assertEqual(Department.objects.count(), 0)
        self.assertTrue(self.tsr.success_ids)
        self.assertTrue(self.tsr.save_list)
        self.tsr.update_db()
        self.assertFalse(School.objects.filter(department_scraped=False).exists())
        self.assertTrue(School.objects.get(department_scraped=True).school_id, 2)
        self.assertEqual(Department.objects.count(), 4)
        self.assertFalse(self.tsr.work_with_db)
        self.assertFalse(self.tsr.success_ids)
        self.assertFalse(self.tsr.save_list)

    def test_append(self):
        self.assertFalse(self.tsr.success_ids)
        self.assertFalse(self.tsr.save_list)
        self.tsr.append(fetched_url=self.furl)
        self.assertEqual(len(self.tsr.success_ids), 1)
        self.assertEqual(self.tsr.success_ids[0], 2)
        self.assertEqual(len(self.tsr.save_list), 4)

    def test_append_update_db(self):
        self.assertFalse(self.tsr.success_ids)
        self.assertFalse(self.tsr.save_list)
        self.assertFalse(School.objects.filter(department_scraped=True).exists())
        self.assertEqual(Department.objects.count(), 0)
        self.tsr.save_count = 1
        self.tsr.append(fetched_url=self.furl)
        self.assertFalse(self.tsr.success_ids)
        self.assertFalse(self.tsr.save_list)
        self.assertTrue(School.objects.get(department_scraped=True).school_id, 2)
        self.assertEqual(Department.objects.count(), 4)


class ExecutorTest(TestCase):
    def setUp(self):
        mommy.make(School, school_id=1)
        mommy.make(School, school_id=2)
        mommy.make(School, school_id=3)
        config = {'fetcher': {'fetch_class': School}, 'saver': {'save_count': 100, 'save_class': Department}}
        self.ter = Loader(fetcher_cls=BaseFetcher, saver_cls=BaseSaver, config=config)

    def tearDown(self):
        School.objects.all().delete()
        Department.objects.all().delete()
        del self.ter

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_execute(self, mocked_get):
        self.assertFalse(School.objects.filter(department_scraped=True).exists())
        self.assertEqual(Department.objects.count(), 0)
        self.ter.load()
        self.assertEqual(School.objects.filter(department_scraped=False).count(), 1)
        sc_error = School.objects.get(department_scraped=False)
        self.assertEqual(sc_error.school_id, 3)
        self.assertEqual(School.objects.filter(department_scraped=True).count(), 2)
        self.assertEqual(Department.objects.count(), 4)


class PaginatedDataGetterTest(TestCase):
    def setUp(self):
        self.tdg = PaginatedFetcher()

    def tearDown(self):
        School.objects.all().delete()
        del self.tdg

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_paginated(self, mock_get):
        paginated = 'https://www.myedu.com/adms/school/paginated'
        self.assertEqual(self.tdg.pages, 1)
        self.assertTrue(self.tdg.is_paginated(url=paginated))
        self.assertEqual(self.tdg.pages, 2)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_not_paginated(self, mock_get):
        not_paginated = 'https://www.myedu.com/adms/school/notpaginated'
        self.assertEqual(self.tdg.pages, 1)
        self.assertFalse(self.tdg.is_paginated(url=not_paginated))
        self.assertEqual(self.tdg.pages, 1)

    def test_get_urls(self):
        urls = list(self.tdg.get_urls())
        self.assertEqual(len(urls), self.tdg.pages)
        for url in urls:
            self.assertIsInstance(url, Url)
            self.assertIn('page', url.url)
            self.assertRegex(url.url, 'https://www.myedu.com/adms/school/\?page=[\d+]')


class PaginatedDataExecutorTest(TestCase):
    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_process_urls(self, mock_get):
        self.assertFalse(School.objects.exists())
        config = {'saver': {'save_count': 100, 'save_class': School}}
        Loader(fetcher_cls=PaginatedFetcher, saver_cls=BaseSaver, config=config).load()
        self.assertTrue(School.objects.exists())
        self.assertEqual(School.objects.count(), 10)
