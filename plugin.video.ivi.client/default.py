# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

from future.utils import iteritems
from simplemedia import py2_decode
import simplemedia
import xbmc
import xbmcplugin

from resources.lib.ivi import IVI


plugin = simplemedia.RoutedPlugin()
_ = plugin.initialize_gettext()

api = None

@plugin.route('/')
def root():
    if plugin.params.action is not None:
        if plugin.params.action == 'search':
            search()
    else:
        plugin.create_directory(_list_root())


def _list_root():

    try:
        categories = _categories()
    except api.APIException as e:
        plugin.notify_error(e.msg)
        categories = {}

    for key, _category in iteritems(categories):
        if _category['id'] in [18]:
            continue
        url = plugin.url_for('category', category_hru=key)
        list_item = {'label': _category['title'],
                     'url': url,
                     'icon': plugin.icon,
                     'fanart': plugin.fanart,
                     'content_lookup': False,
                     }
        yield list_item

    url = plugin.url_for('search_history')
    list_item = {'label': _('Search'),
                 'url': url,
                 'icon': plugin.get_image('DefaultAddonsSearch.png'),
                 'fanart': plugin.fanart,
                 'content_lookup': False,
                 }
    yield list_item


@plugin.mem_cached(180)
def _categories():
    result = {}
    for _category in api.categories():
        result[_category['hru']] = _category

    return result


@plugin.route('/category/<category_hru>')
def category(category_hru):
    _category = _categories()[category_hru]

    step = plugin.params.get('step', plugin.get_setting('step', False))
    step = int(step)
    start = plugin.params.get('from', '0')
    start = int(start)
    params = {'from': start,
              }

    try:
        category_info = api.catalogue(_category['id'], step, **params)
        params = {'items': _list_category(category_info, category_hru),
                  'total_items': category_info['count'],
                  'content': 'movies',
                  'category': _category['title'],
                  'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
                  'update_listing': (start > 0),

                  }
    except api.APIException as e:
        plugin.notify_error(e.msg)
        params = {'items': [],
                  'succeeded': False,
                  }

    plugin.create_directory(**params)


def _list_category(data, category_hru=''):

    use_pages = (category_hru != '')

    for item in data['list']:
        listitem = _get_listitem(item)
        yield listitem

    page_params = {}
    page_params.update(plugin.params)
    page_params['step'] = data['step']

    if use_pages \
      and data['from'] >= data['step']:
        page_params['from'] = data['from'] - data['step']
        if page_params['from'] == 0:
            del page_params['from']

        url = plugin.url_for('category', category_hru=category_hru, **page_params)
        item_info = {'label': _('Previous page...'),
                     'url':   url}
        yield item_info

    if use_pages \
      and data['total'] >= data['from'] + data['step']:
        page_params['from'] = data['from'] + data['step']
        url = plugin.url_for('category', category_hru=category_hru, **page_params)
        item_info = {'label': _('Next page...'),
                     'url':   url}
        yield item_info


@plugin.route('/compilation/<compilation_id>')
def compilation(compilation_id):

    try:
        compilation_info = api.compilationinfo(compilation_id)

        params = {'items': _list_seasons(compilation_info),
                  'total_items': compilation_info['seasons_count'],
                  'content': 'seasons',
                  'category': compilation_info['title'],
                  'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS, 'label2Mask': '%Y / %O'},
                  }
    except api.APIException as e:
        plugin.notify_error(e.msg)
        params = {'items': [],
                  'succeeded': False,
                  }

    plugin.create_directory(**params)


def _list_seasons(data):
    item = {}
    item.update(data)
    del item['seasons']
    del item['seasons_content_total']
    del item['seasons_count']
    del item['seasons_description']

    for season in data['seasons']:
        item['object_type'] = 'season'

        season_str = str(season)
        season_description = data['seasons_description'].get(season_str)
        season_content_total = data['seasons_content_total'].get(season_str, 0)

        if season_description:
            item['description'] = season_description
        item['season_content_total'] = season_content_total
        item['season'] = season

        listitem = _get_listitem(item)
        yield listitem


@plugin.route('/compilation/<compilation_id>/', 'compilation_season_short')
@plugin.route('/compilation/<compilation_id>/<season>')
def compilation_season(compilation_id, season=None):
    try:
        season_info = api.videofromcompilation(compilation_id, season)

        params = {'items': _list_episodes(season_info),
                  'total_items': season_info['count'],
                  'content': 'episodes',
    #              'category': season_info['title'],
                  'sort_methods': xbmcplugin.SORT_METHOD_EPISODE,
                  'cache_to_disk': True,
                  }
    except api.APIException as e:
        plugin.notify_error(e.msg)
        params = {'items': [],
                  'succeeded': False,
                  }

    plugin.create_directory(**params)


def _list_episodes(data):

    for item in data['list']:
        listitem = _get_listitem(item)
        yield listitem


def _get_listitem(item):
    properties = {}
    video_info_upd = {}
    orig_title = ''
    countries = _countries()

    country = []
    if isinstance(item['country'], list):
        for _country in item['country']:
            country.append(countries[_country]['title'])
    elif isinstance(item['country'], int):
            country.append(countries[item['country']]['title'])

    genre = []
    for _genre in item['genres']:
        genre_title = _get_genre(item['categories'][0], _genre)
        if genre_title:
            genre.append(genre_title)

    ratings = _get_ratings(item)

    rating = 0
    for _rating in ratings:
        if _rating['defaultt']:
            rating = _rating['rating']
            break

    if item['object_type'] == 'video':
        url = plugin.url_for('play_video', video_id=item['id'])
        is_folder = False
        is_playable = True
        if item.get('episode') is None:
            title = item['title']
            orig_title = item['orig_title']
            mediatype = 'movie'

            video_info_upd = {'duration': item['duration_minutes'] * 60,
                              }
        else:
            title = item['title']
            mediatype = 'episode'

            season = max(item.get('season', 0), 1)
            video_info_upd = {'duration': item['duration_minutes'] * 60,
                              'tvshowtitle': item['compilation_title'],
                              'episode': item['episode'],
                              'season': season,
                              'sortepisode': item['episode'],
                              'sortseason': season,
                              }

    elif item['object_type'] == 'compilation':
        if item['seasons_count'] == 0:
            url = plugin.url_for('compilation_season_short', compilation_id=item['id'])
        else:
            url = plugin.url_for('compilation', compilation_id=item['id'])
        mediatype = 'tvshow'
        is_folder = True
        is_playable = False
        title = item['title']
        orig_title = item['orig_title']

        properties = {'TotalSeasons': str(max(item['seasons_count'], 1)),
                      'TotalEpisodes': str(item['total_contents']),
                      'WatchedEpisodes': '0',
                      }

    elif item['object_type'] == 'season':
        url = plugin.url_for('compilation_season', compilation_id=item['id'], season=item['season'])
        mediatype = 'season'
        is_folder = True
        is_playable = False
        title = '{0} {1}'.format(_('Season'), item['season'])

        properties = {'TotalEpisodes': str(item['total_contents']),
                      'WatchedEpisodes': '0',
                      }

        video_info_upd = {'tvshowtitle': item['title'],
                          'season': item['season'],
                          'sortseason': item['season'],
                          }

    mpaa = api.get_age_restricted_rating(item.get('restrict'), 'rars')

    video_info = {'title': title,
                  'originaltitle': orig_title if orig_title else title,
                  'sorttitle': title,
                  'year': item['year'],
                  'plot': plugin.remove_html(item['description']),
                  'plotoutline': plugin.remove_html(item['synopsis']),
                  'mpaa': mpaa,
                  'premiered': item['release_date'],
                  'mediatype': mediatype,
                  'cast': item['artists'],
                  'country': country,
                  'genre': genre,
                  'rating': rating,
                  }
    video_info.update(video_info_upd)

    listitem = {'label': title,
#                'ratings': ratings,
                'info': {'video': video_info,
                         },
                'art': {'poster': item.get('poster')},
                'fanart':  item.get('thumb', plugin.fanart),
                'thumb':  item.get('thumb'),
                'content_lookup': False,
                'is_folder': is_folder,
                'is_playable': is_playable,
                'url': url,
                'properties': properties,
                'ratings': ratings,
                }

    return listitem


@plugin.route('/watch/<video_id>')
def play_video(video_id):
    succeeded = True

    try:
        video_info = api.videoinfo(video_id)
        listitem = _get_listitem(video_info)

        videolinks = api.videolinks(video_id)
        listitem['path'] = _get_video_path(videolinks)
    except api.APIException as e:
        plugin.notify_error(e.msg)
        succeeded = False
        listitem = {}

    plugin.resolve_url(listitem, succeeded)


def _get_video_path(links):

    video_quality = plugin.get_setting('video_quality')

    path = ''
    if (not path or video_quality >= 0) and links.get('MP4-lo') is not None:
        path = links['MP4-lo']
    if (not path or video_quality >= 1) and links.get('MP4-hi') is not None:
        path = links['MP4-hi']
    if (not path or video_quality >= 2) and links.get('MP4-SHQ') is not None:
        path = links['MP4-SHQ']
    if (not path or video_quality >= 3) and links.get('MP4-HD720') is not None:
        path = links['MP4-HD720']
    if (not path or video_quality >= 4) and links.get('MP4-HD1080') is not None:
        path = links['MP4-HD1080']

    return path


@plugin.route('/search/history')
def search_history():

    with plugin.get_storage('__history__.pcl') as storage:
        history = storage.get('history', [])

        if len(history) > plugin.get_setting('history_length'):
            history[plugin.history_length - len(history):] = []
            storage['history'] = history

    listing = []
    listing.append({'label': _('New Search...'),
                    'url': plugin.url_for('search'),
                    'icon': plugin.get_image('DefaultAddonsSearch.png'),
                    'fanart': plugin.fanart})

    for item in history:
        listing.append({'label': item['keyword'],
                        'url': plugin.url_for('search', keyword=item['keyword']),
                        'icon': plugin.icon,
                        'fanart': plugin.fanart})

    plugin.create_directory(listing, content='files', category=_('Search'))


@plugin.route('/search')
def search():

    keyword = plugin.params.keyword or ''
    usearch = (plugin.params.usearch == 'True')

    new_search = (keyword == '')

    if not keyword:
        kbd = xbmc.Keyboard('', _('Search'))
        kbd.doModal()
        if kbd.isConfirmed():
            keyword = kbd.getText()

    if keyword and new_search and not usearch:
        with plugin.get_storage('__history__.pcl') as storage:
            history = storage.get('history', [])
            history.insert(0, {'keyword': keyword})
            if len(history) > plugin.get_setting('history_length'):
                history.pop(-1)
            storage['history'] = history

        url = plugin.url_for('search', keyword=py2_decode(keyword))
        xbmc.executebuiltin('Container.Update("%s")' % url)

    elif keyword:
        videos_info = api.search(keyword)
        plugin.create_directory(_list_search(videos_info), content='movies', category=_('Search'))


def _list_search(data):

    for item in data['list']:
        listitem = _get_listitem(item)
        yield listitem


def _init_api():
    global api

    app_version = plugin.get_setting('app_version')
    subsite_id = plugin.get_setting('subsite_id', False)
    session = plugin.get_setting('session')
    user_ab_bucket = plugin.get_setting('user_ab_bucket')
    user_uid = plugin.get_setting('user_uid')
    api = IVI(app_version)

    if not user_uid:
        user_uid = IVI.get_uid()
        plugin.set_setting('user_uid', user_uid)
    api.set_prop('uid', user_uid)

    try:
        if not session:
            session_info = api.get_session()
            session = session_info['session']
            user_ab_bucket = session_info['user_ab_bucket']

            plugin.set_setting('session', session)
            plugin.set_setting('user_ab_bucket', user_ab_bucket)

        api.set_prop('user_ab_bucket', user_ab_bucket)
        api.set_prop('session', session)

        geo_info = _api_geocheck()
        if geo_info['actual_app_version'] != app_version:
            plugin.set_setting('app_version', geo_info['actual_app_version'])
            api.set_prop('app_version', geo_info['actual_app_version'])

        if geo_info['user_ab_bucket'] != user_ab_bucket:
            plugin.set_setting('user_ab_bucket', geo_info['user_ab_bucket'])
            api.set_prop('user_ab_bucket', geo_info['user_ab_bucket'])

        app_info = _api_appinfo()
        if app_info['subsite_id'] != subsite_id:
            plugin.set_setting('subsite_id', app_info['subsite_id'])
            api.set_prop('subsite_id', app_info['subsite_id'])

    except api.APIException as e:
        plugin.notify_error(e.msg)

    session = plugin.get_setting('session', False)
    api.set_prop('session', session)

    api.set_prop('key', 'f10232b7bc5c7ae8f796c1332b27a18c')
    api.set_prop('key1', 'e9044861170176cc')
    api.set_prop('key2', 'd20890c22e02ed83')


@plugin.mem_cached(60)
def _api_geocheck():
    return api.geocheck()


@plugin.mem_cached(60)
def _api_appinfo():
    return api.appversioninfo()


@plugin.mem_cached(60)
def _countries():
    countries = api.countries()
    items = {}
    for country in countries:
        items[int(country['id'])] = country

    return items


@plugin.mem_cached(60)
def _get_genre(category_id, genre_id):
    categories = _categories()
    for key_c, category in iteritems(categories):
        if category['id'] == category_id:
            for key_g, genre in iteritems(category['genres']):
                if genre['id'] == genre_id:
                    return genre['title']
    return ''


def _get_rating_source():
    rating_source = plugin.get_setting('video_rating')
    if rating_source == 0:
        source = 'ivi'
    elif rating_source == 1:
        source = 'imdb'
    elif rating_source == 2:
        source = 'kinopoisk'
    return source


def _rating_sources():
    yield {'rating_source': 'kinopoisk',
           'field': 'kp',
           }
    yield {'rating_source': 'imdb',
           'field': 'imdb',
           }
    yield {'rating_source': 'ivi',
           'field': 'ivi',
           }


def _get_ratings(item):
    default_source = _get_rating_source()
    items = []
    for rating in _rating_sources():
        rating_item = _make_rating(item, **rating)
        rating_item['defaultt'] = (rating_item['type'] == default_source)
        items.append(rating_item)

    return items


def _make_rating(item, rating_source, field):
    keys = [field, 'rating']
    rating_field = '_'.join(keys)

    rating = item.get(rating_field, '0')
    if rating:
        rating = float(rating)
    else:
        rating = 0

    return {'type': rating_source,
            'rating': rating,
            'votes': 0,
            'defaultt': False,
            }


if __name__ == '__main__':
    _init_api()
    plugin.run()
