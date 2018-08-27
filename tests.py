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

mock_inputstreamhelper = mock.MagicMock()

sys.modules['inputstreamhelper'] = mock_inputstreamhelper


def tearDownModule():
    shutil.rmtree(config_dir, True)


class PluginActionsTestCase(unittest.TestCase):

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/login'.format(addon_name), '0', ''])
    def test_00_login():
        print('# test_login')
        xbmc.Keyboard.strings.append('c1700697@nwytg.net')
        xbmc.Keyboard.strings.append('123456')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/'.format(addon_name), '1', ''])
    def test_01_root():
        print('# test_root')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/category/series'.format(addon_name), '2', ''])
    def test_02_category():
        print('# test_category')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/compilation/9591'.format(addon_name), '3', ''])
    def test_03_compilation():
        print('# test_compilation')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/compilation/9591/2'.format(addon_name), '4', ''])
    def test_04_compilation_season():
        print('# test_compilation_season')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/compilation/7312/'.format(addon_name), '5', ''])
    def test_05_compilation_season_short():
        print('# test_compilation_season_short')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/watch/176712'.format(addon_name), '6', ''])
    def test_06_watch():
        print('# test_watch')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search'.format(addon_name), '7', ''])
    def test_07_search():
        print('# test_search')
        xbmc.Keyboard.strings.append('Смешарики')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/search/history'.format(addon_name), '8', ''])
    def test_08_search_history():
        print('# test_search_history')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/favourites'.format(addon_name), '9', ''])
    def test_09_favourites():
        print('# test_favourites')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/watchhistory'.format(addon_name), '10', ''])
    def test_10_watchhistory():
        print('# test_watchhistory')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/unfinished'.format(addon_name), '11', ''])
    def test_11_unfinished():
        print('# test_unfinished')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/purchases'.format(addon_name), '12', ''])
    def test_12_purchases():
        print('# test_purchases')
        imp.load_source('__main__', default_script)

    @staticmethod
    @mock.patch('simpleplugin.sys.argv', ['plugin://{0}/logout'.format(addon_name), '13', ''])
    def test_13_logout():
        print('# test_logout')
        imp.load_source('__main__', default_script)


if __name__ == '__main__':
    unittest.main()
