
from datetime import datetime, timedelta
#import requests
import re
import urllib

import json
import FDB

class Crawler:

    def __init__(self, base_url):
        self.base_url = base_url
        self.cache =  None
    def get_file(self, filename):
        with open(filename) as f:
            self.cache = json.load(f)
    def get_json(self, url):
        if self.cache:
            return self.cache
        data = dohresolver.doh_session().get(url).json()
        self.cache = data
        # TODO put text up into obj store
        return data
    def parse_json(self):
        self.videos = [Video(x) for x in self.cache]
    def push2db(self, db):
        for v in self.videos:
            db.doit("MERGE (:Person {name: $name})", name=v.person)
            db.doit("MERGE (:Video {name: $name, site: $site, length: $length})", name=v.videoName, site=v.siteName, length=v.length)
            urls = self.get_urls(v)
            db.doit("MERGE (:Instance {url: $url, type: 'image'})", url=urls['image'])
            db.doit("MERGE (:Instance {url: $url, type: 'video', qual: $qual})", url=urls['video'], qual=v.qual[-1])
            db.doit("MATCH (m:Person {name: $person}) MATCH (v:Video {name: $video}) MERGE (m)-[:ACTS_IN]->(v)", video=v.videoName, person=v.person)
            db.doit("MATCH (i:Instance {url: $url}) MATCH (v:Video {name: $name}) MERGE (i)-[:INST_OF]->(v)", name=v.videoName, url=urls['image'])
            db.doit("MATCH (i:Instance {url: $url}) MATCH (v:Video {name: $name}) MERGE (i)-[:INST_OF]->(v)", name=v.videoName, url=urls['video'])


class Video:
    def _parsetime(self, stringy):
        mg = re.match('^\D*(\d+)\D+(\d+)\D*', stringy)
        minutes = mg.group(1)
        seconds = mg.group(2)
        return timedelta(minutes=int(minutes), seconds=int(seconds))

    def __init__(self, dictin):
        self.id = dictin['id']
        self.videoName = dictin['videoName']
        self.length = self._parsetime(dictin['videoLength'])
        self.siteName = dictin['siteName']
        self.qual = []
        for i in []:
            if dictin['version' + i]:
                self.qual.append(i.lower())
        if dictin['updatedDate']:
            self.updated = datetime.fromisoformat(dictin['updatedDate'])
        else:
            self.updated = None
    
    def thumb_name(self):
        return self.siteName + ' ' + self.videoName + '.jpg'

    def file_name(self):
        return self.siteName + ' ' + self.videoName + ' ' + self.qual[-1] + '.mp4'

bla = Crawler()
bla.get_file()
bla.parse_json()
bla.push2db(FDB.DB('bolt://0.0.0.0/', ('neo4j','test')))
