from neo4j.v1 import GraphDatabase

class DB:
    def __init__(self, uri, auth):
        self._driver = GraphDatabase.driver(uri, auth=auth)
    def close(self):
        self._driver.close()
    def doit(self, it, **kwargs):
        with self._driver.session() as session:
            return session.run(it, **kwargs)



