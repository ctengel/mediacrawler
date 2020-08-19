
"""Base Thing which most else descends"""

from uuid import uuid4, UUID
import mcurl


class Thing:
    """Thing abstract class which handles urls, ids, and parent-child"""
    typ = None

    def __init__(self):
        idish = None
        self._uuid = None
        self.set_uuid()
        self.parents = []
        self.children = []
        self.set_id(idish)
        self.name = None
        self.extra = {}
        self.urls = []

    def set_uuid(self, uuid=None):
        """Set a new UUID"""
        if self._uuid:
            raise Exception('Cannot overwrite UUID: '
                            'UUID {}, type {}, absid {}'.format(self._uuid,
                                                                self.typ,
                                                                self.absid))
        if not uuid:
            uuid = uuid4()
        if not isinstance(uuid, UUID):
            uuid = UUID(uuid)
        self._uuid = uuid

    def get_uuid(self):
        """Get UUID"""
        return self._uuid

    def _obtain_id(self, idish):
        # override to resolve conflicts
        return idish

    def set_id(self, idish):
        """Set ID and absID based on an id-like value"""
        self.idn = self._obtain_id(idish)
        self.absid = self.parents[0].id + '/' + self.typ + '/' + self.idn
        self.idish = idish
        return self.idn, self.absid

    def add_url(self, url, rel=None, primary=False):
        """Add URL for this object"""
        # abstract out list stuff
        newurl = mcurl.URL(url, rel)
        if url in [x.href for x in self.urls if x.rel == rel]:
            if primary:
                # find and remove it
                pass
        else:
            if primary:
                self.urls.insert(0, newurl)
            else:
                self.urls.append(newurl)
    # dictout and stringout
