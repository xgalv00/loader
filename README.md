# Simple scraper 

Goal is to explore new ways of concurrent loading

Try to create simple decoupled scraper, that actually loading process could be easily changed.
And fetching is isolated from saving.



## TODO

- Replace blocking call to requests.get method with the smallest change to the api possible. (possible variants - grequests, aiohttp, requests-futures)
- Use concurrent.futures instead of asyncio loader

## Install notes

- git clone git@github.com:xgalv00/loader.git
- virtualenv -p python3 env
- source env/bin/activate
- cd loader
- pip install -r requirements/requirements.txt
- python manage.py migrate