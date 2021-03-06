from django.db import models


class BaseScrapeModel(models.Model):
    UID = models.PositiveIntegerField()

    datasource_code = models.CharField(max_length=100, null=True)
    datasource_id = models.PositiveIntegerField(null=True)
    datasource_user_id = models.PositiveIntegerField(null=True)

    source_url = models.CharField(max_length=500, default='')

    class Meta:
        abstract = True


class BaseSchoolModel(BaseScrapeModel):
    school_id = models.PositiveIntegerField()
    school_name = models.CharField(max_length=500, null=True)

    class Meta:
        abstract = True


class School(BaseSchoolModel):

    # search field but could be null
    abbreviation = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=200, null=True)
    active = models.NullBooleanField()
    campus_setting = models.CharField(max_length=200, null=True)
    city = models.CharField(max_length=200, null=True)
    color = models.CharField(max_length=200, null=True)
    mascot = models.CharField(max_length=200, null=True)
    common_name = models.CharField(max_length=200, null=True)
    edu_time = models.CharField(max_length=200, null=True)
    edu_type = models.CharField(max_length=200, null=True)
    education_network_member = models.CharField(max_length=200, null=True)
    has_grades = models.NullBooleanField()
    graduate_population = models.PositiveIntegerField(null=True)
    launch_group_code = models.CharField(max_length=200, null=True)
    launch_group_id = models.PositiveIntegerField(null=True)
    launch_priority = models.PositiveIntegerField(null=True)
    launch_status_code = models.CharField(max_length=200, null=True)
    launch_status_id = models.PositiveIntegerField(null=True)
    on_campus_avail = models.NullBooleanField()
    no_registration = models.NullBooleanField()
    parent_school_id = models.PositiveIntegerField(null=True)
    revenue = models.NullBooleanField()
    school_bucket = models.CharField(max_length=100, null=True)
    school_seo_title = models.CharField(max_length=200, null=True)
    school_seo_url = models.CharField(max_length=200, null=True)
    school_seo_description = models.TextField(null=True)
    course_by_dept_seo_url = models.CharField(max_length=200, null=True)
    degree_by_college_seo_url = models.CharField(max_length=200, null=True)
    prof_by_dept_seo_url = models.CharField(max_length=200, null=True)
    school_type = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=100, null=True)
    undergraduate_population = models.PositiveIntegerField(null=True)
    zip = models.CharField(max_length=100, null=True)
    registration_url = models.CharField(max_length=200, null=True)
    degree_audit_url = models.CharField(max_length=200, null=True)
    department_scraped = models.BooleanField(default=False)


class Department(BaseSchoolModel):
    abbreviation = models.CharField(max_length=100, null=True)
    department_id = models.PositiveIntegerField()
    department_course_seo_url = models.CharField(max_length=200, null=True)
    department_professor_seo_url = models.CharField(max_length=200, null=True)
    name = models.CharField(max_length=200, null=True)
    school_abbrev = models.CharField(max_length=100, null=True)
    course_scraped = models.BooleanField(default=False)
    professor_scraped = models.BooleanField(default=False)


class Professor(BaseSchoolModel):
    department_abbreviation = models.CharField(max_length=100, null=True)
    department_id = models.PositiveIntegerField()
    department_name = models.CharField(max_length=200, null=True)
    first_name = models.CharField(max_length=100, null=True)
    grade_count = models.PositiveIntegerField()
    last_name = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=200, null=True)
    professor_full_image = models.CharField(max_length=400, null=True)
    professor_id = models.PositiveIntegerField()
    professor_thumb_image = models.CharField(max_length=450, null=True)
    recommendation_count = models.PositiveIntegerField(null=True)
    school_abbrev = models.CharField(max_length=100, null=True)
    seo_url = models.CharField(max_length=500, null=True)
    professor_seo_title = models.CharField(max_length=500, null=True)
    professor_seo_description = models.TextField(null=True)
    professor_seo_url = models.CharField(max_length=600, null=True)
    show_grades = models.NullBooleanField()
    user_id = models.PositiveIntegerField(null=True)
    withdraw_average = models.FloatField(null=True)


class Course(BaseSchoolModel):
    abbreviation = models.CharField(max_length=100, null=True)
    average_class_size = models.PositiveIntegerField(null=True)
    common_course_id = models.PositiveIntegerField(null=True)
    course_id = models.PositiveIntegerField()
    course_name = models.CharField(max_length=400, null=True)
    course_number = models.CharField(max_length=20, null=True)
    course_seo_url = models.CharField(max_length=500, null=True)
    course_seo_title = models.CharField(max_length=400, null=True)
    course_seo_description = models.TextField(null=True)
    credit_hours = models.PositiveIntegerField(null=True)
    department_id = models.PositiveIntegerField(db_index=True)
    dept_abbreviation = models.CharField(max_length=100, null=True)
    dept_category_code = models.CharField(max_length=100, null=True)
    parent_dept_category_code = models.CharField(max_length=100, null=True)
    dept_name = models.CharField(max_length=300, null=True)
    description = models.TextField(null=True)
    grade_count = models.PositiveIntegerField(null=True)
    import_id = models.PositiveIntegerField(null=True)
    overall_gpa = models.FloatField(null=True)
    quality_check = models.NullBooleanField()
    recommendation_count = models.PositiveIntegerField(null=True)
    school_abbrev = models.CharField(max_length=100, null=True)
    school_bucket = models.CharField(max_length=100, null=True)
    modified = models.CharField(max_length=100, null=True)

    class Meta:
        index_together = ['school_id', 'department_id', 'course_number']
