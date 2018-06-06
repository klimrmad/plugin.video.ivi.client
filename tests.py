# coding: utf-8
# Module: tests

from __future__ import print_function, unicode_literals
import os
import sys
import unittest
import imp
import mock
import shutil
import xbmcaddon
import xbmc
import simpleplugin

addon_name = 'plugin.video.ivi.client'

cwd = os.path.dirname(os.path.abspath(__file__))
config_dir = os.path.join(cwd, 'config')
addon_dir = os.path.join(cwd, addon_name)

xbmcaddon.init_addon(addon_dir, config_dir, True)

# prepare search history
addon = simpleplugin.Addon()
with addon.get_storage('__history__.pcl') as storage:
    history = storage.get('history', [])
    history.insert(0, {'keyword': 'Нюхач'})
    storage['history'] = history

xbmc._set_log_level(-1)

default_script = os.path.join(addon_dir, 'default.py')

# Import our module being tested
sys.path.append(addon_dir)


def tearDownModule():
    shutil.rmtree(config_dir, True)


class PluginActionsTestCase(unittest.TestCase):

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/'.format(addon_name), '1', ''])
    def test_root():
        print('# test_root')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/category/series'.format(addon_name), '2', ''])
    def test_category():
        print('# test_category')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/compilation/9591'.format(addon_name), '3', ''])
    def test_compilation():
        print('# test_compilation')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/compilation/9591/2'.format(addon_name), '4', ''])
    def test_compilation_season():
        print('# test_compilation_season')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/compilation/7312/'.format(addon_name), '5', ''])
    def test_compilation_season_short():
        print('# test_compilation_season_short')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/watch/176712'.format(addon_name), '6', ''])
    def test_watch():
        print('# test_watch')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search'.format(addon_name), '7', '?keyword=Нюхач'])
    def test_search():
        print('# test_search')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search/history'.format(addon_name), '8', ''])
    def test_search_history():
        print('# test_search_history')
        imp.load_source('__main__', default_script)


if __name__ == '__main__':
    unittest.main()
