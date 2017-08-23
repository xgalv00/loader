--  11362
SELECT count(*) from scraper_school;
SELECT count(*) FROM scraper_school WHERE department_scraped=0;
-- UPDATE scraper_school SET department_scraped=0;

-- 110101
SELECT count(*) from scraper_department;
-- 110027
SELECT count(*) from scraper_department WHERE course_scraped=1;
-- 109973
SELECT count(*) from scraper_department WHERE professor_scraped=1;
-- UPDATE scraper_department SET professor_scraped=0,course_scraped=0;


SELECT count(*) from scraper_course;
SELECT count(*) from scraper_professor;

-- DELETE FROM scraper_school;
-- DELETE FROM scraper_department;
-- DELETE FROM scraper_course;
-- DELETE FROM scraper_professor;