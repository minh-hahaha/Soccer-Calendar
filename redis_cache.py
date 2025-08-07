import redis
import os
from dotenv import load_dotenv
import json

load_dotenv()

r = redis.Redis.from_url(os.getenv("REDIS_URL"))

def get_cache(key):
    data = r.get(key)
    if data:
        return json.loads(data)
    return None

# set cache with key and data and 3600 seconds = 1 hour
def set_cache(key, data, ttl=3600):
    r.setex(key, ttl, json.dumps(data))
    