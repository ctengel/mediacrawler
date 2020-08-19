#!/usr/bin/env python3
"""Different tools for indexing media in files"""

from pathlib import Path
from typing import Callable, List
import mimetypes
import os
import argparse
import uuid
import json
import warnings
import hashlib
import magic

BUF = 1024 * 1024


class Error(Exception):
    """Base error class"""


class NotMyKindOfFile(Error):
    """Error if file is miscategorized"""
    def __init__(self, path, attempted):
        """Include path and class attempted"""
        super().__init__(self)
        self.path = path
        self.attempted = attempted


class File:
    """Generic file object, providing slightly more info than a pathlib.Path"""
    file_type = 'file'
    readfile = True
    mimepre = None

    @classmethod
    def get_media(cls, path: Path, tree=None) -> 'File':
        """Return a specific as possible object"""
        new_cls = cls._determine_type(path)
        try:
            return new_cls(path, tree)
        except NotMyKindOfFile as exp:
            warnings.warn("{} is not a {}".format(exp.path, exp.attempted))
            return cls(path, tree)

    @staticmethod
    def get_ext_mime(path):
        """Return a MIME of a given path based on extension"""
        return mimetypes.guess_type(path)[0]

    @classmethod
    def _determine_type(cls, path: Path) -> Callable[[Path], 'File']:
        """Given a path, determine file type info"""
        if path.is_symlink():
            return SymLink
        if path.is_dir():
            return Directory
        assert path.is_file()  # TODO do something with special files?
        mimext = cls.get_ext_mime(path)
        if not mimext:
            return cls
        for attmpt in Image, Video, Audio:
            if mimext.startswith(attmpt.mimepre):
                return attmpt
        # TODO scan for archives, isos, etc
        return cls

    @staticmethod
    def pfm(path):
        """PFM: get mime type from file"""
        # TODO compare with filetype
        return magic.detect_from_filename(path).mime_type

    def magic_file(self):
        """Get best magic for this file"""
        if not self.readfile:
            self.mime = None
            return
        self.mime = self.pfm(self.path)
        if not self.mime:
            self.mime = self.get_ext_mime(self.path)
        if self.mimepre:
            if not self.mime.startswith(self.mimepre):
                raise NotMyKindOfFile(self.path, self.file_type)

    @staticmethod
    def sha256sum(path):
        """Get SHA256 of given path"""
        sha = hashlib.sha256()
        with open(path, 'rb') as flh:  # TODO use Path method
            while True:
                data = flh.read(BUF)
                if not data:
                    break
                sha.update(data)
        return sha.hexdigest()

    def hash_file(self):
        """Store hash"""
        if not self.readfile:
            self.sha256 = None
            return
        self.sha256 = self.sha256sum(self.path)

    def __init__(self, path: Path, tree=None):
        self.path = path
        self.tree = tree
        self.status()
        self.magic_file()
        self.hash_file()
        self.type_init()

    def type_init(self):
        """Override this to do type-specific stuff at init"""

    def asdict(self):
        """Return dictionary suitable for JSON"""
        return {'type': self.file_type,
                'path': self.path.relative_to(self.tree.path)
                        if self.tree else self.path,
                'size': self.stat.st_size,
                'mtime': self.stat.st_mtime,
                'mime': self.mime,
                'sha256': self.sha256}

    def status(self):
        """Default stat for non-links, use Pathlib"""
        self.stat = self.path.stat()


# Special file types


class SymLink(File):
    """A symlink with basic info on target file"""
    file_type = 'symlink'
    readfile = False

    def status(self):
        """Override stat for symlinks - go straight to OS"""
        self.stat = os.stat(self.path, follow_symlinks=False)

    def type_init(self):
        self.target = self.path.resolve()

    def asdict(self):
        base = super().asdict()
        base['target'] = self.target
        return base


class Directory(File):
    """A directory, with contents

    See DirTree for more stuff like that
    """
    file_type = 'dir'
    readfile = False


# Normal file types


class Archive(File):
    """Archive"""
    file_type = 'archive'


class Image(File):
    """Image, with things like EXIF, face recognition, etc"""
    file_type = 'image'
    mimepre = 'image/'


class Audio(File):
    """Audio file, with ID3, etc"""
    file_type = 'audio'
    mimepre = 'audio/'


class Video(Audio, Image):
    """Both audio and images, screencaps, etc"""
    file_type = 'video'
    mimepre = 'video/'


# DirTree and FSTree


class DirTree:
    """Recurse through a dirtree"""
    tree_type = 'subtree'

    def __init__(self, path: Path):
        self.uuid = uuid.uuid1()
        self.path = path
        self.files = None
        self.load_files()

    @staticmethod
    def _joinpaths(root: str, children: List[str]) -> List[Path]:
        """Make a list of Path objects from a base of children"""
        return [Path(root, x) for x in children]

    def read_tree(self):
        """Walk through a tree, returning a flat list of Path objects"""
        files = [self.path]
        for path, dirs, fls in os.walk(self.path):
            files = files + self._joinpaths(path, dirs) + \
                            self._joinpaths(path, fls)
        return files

    def load_files(self):
        """Load File objects into tree"""
        allfiles = self.read_tree()
        self.files = [File.get_media(x, self) for x in allfiles]

    @classmethod
    def get_tree(cls, path: Path):
        """Return DirTree or FSTree object"""
        if path.resolve().is_mount():  # NOTE resolve needed else . always True
            return FSTree(path)
        return cls(path)

    def asdict(self):
        """Return dict suitable for JSON"""
        return {'root': self.path.resolve(),
                'files': self.files,
                'treeuuid': self.uuid,
                'fs': bool(self.tree_type == 'fstree')}


class FSTree(DirTree):
    """Extra stuff for filesystem"""
    tree_type = 'fstree'
    # TODO add stuff with for instance UUID, type, etc


class JSONEncoder(json.JSONEncoder):
    """Custom JSONEncoder for DirTree and its children"""
    def default(self, o):
        if isinstance(o, (DirTree, File)):
            return o.asdict()
        if isinstance(o, (Path, uuid.UUID)):
            return str(o)
        return super().default(o)


def tree2json(path, jsonf):
    """Given a tree put output in a JSON file"""
    tree = DirTree.get_tree(Path(path))
    with open(jsonf, 'w') as jfh:
        json.dump(tree, jfh, cls=JSONEncoder)


def _cli():
    """CLI"""
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('json')
    args = parser.parse_args()
    tree2json(args.path, args.json)


if __name__ == '__main__':
    _cli()
