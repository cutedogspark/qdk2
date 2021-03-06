#!/usr/bin/env python

from argparse import SUPPRESS
from os import getenv, getcwd
from os.path import (join as pjoin,
                     exists as pexists,
                     abspath as pabspath,
                     )
import os

from basecommand import BaseCommand
from log import info, warning, error
from controlfiles import ControlFile, ChangelogFile
from settings import Settings
from configs import QDKrc
from editor import Editor


class CommandChangelog(BaseCommand):
    key = 'changelog'

    @classmethod
    def build_argparse(cls, subparser):
        parser = subparser.add_parser(cls.key, help='modify QPKG changelog')
        parser.add_argument('--' + cls.key, help=SUPPRESS)
        parser.add_argument('-m', '--message', nargs="*",
                            default=None,
                            help='use the given message(s) as the log message')
        parser.add_argument('-v', '--version',
                            default=None,
                            help='this specifies the version number')

    @property
    def qpkg_dir(self):
        if not hasattr(self, '_qpkg_dir'):
            cwd = getcwd()
            while cwd != '/':
                if pexists(pjoin(cwd, Settings.CONTROL_PATH, 'control')):
                    break
                cwd = pabspath(pjoin(cwd, os.pardir))
            self._qpkg_dir = cwd if cwd != '/' else None
        return self._qpkg_dir

    @property
    def author(self):
        if not hasattr(self, '_author'):
            self._author = getenv('QPKG_NAME')
        return self._author

    @property
    def email(self):
        if not hasattr(self, '_email'):
            self._email = getenv('QPKG_EMAIL')
        return self._email

    def run(self):
        if self.qpkg_dir is None:
            error('Cannot find QNAP/changelog anywhere!')
            error('Are you in the source code tree?')
            return -1

        # read ~/.qdkrc
        qdkrc = QDKrc()
        cfg_user = qdkrc.config['user']

        control = ControlFile(self.qpkg_dir)
        changelog = ChangelogFile(self.qpkg_dir)
        kv = {'package_name': control.source['source']}
        if self._args.message is not None:
            kv['messages'] = self._args.message
        if self._args.version is not None:
            kv['version'] = self._args.version
        kv['author'] = cfg_user['name'] if self.author is None else self.author
        kv['email'] = cfg_user['email'] if self.email is None else self.email
        if len(kv['author']) == 0 or len(kv['email']) == 0:
            warning('Environment variable QPKG_NAME or QPKG_EMAIL are empty')
            info('QPKG_NAME: ' + kv['author'])
            info('QPKG_EMAIL: ' + kv['email'])
            yn = raw_input('Continue? (Y/n) ')
            if yn.lower() == 'n':
                return 0
            kv['author'] = 'noname'
            kv['email'] = 'noname@local.host'
        entry = changelog.format(**kv)

        editor = Editor()
        editor.insert_content(entry)
        editor.open(changelog.filename)
        return 0


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
