# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

from future.utils import iteritems
from simplemedia import py2_decode
import simplemedia
import inputstreamhelper

import xbmc
import xbmcplugin

from resources.lib.ivi import IVI
import xbmcgui

plugin = simplemedia.RoutedPlugin()
_ = plugin.initialize_gettext()

api = None
country = ''


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

    # Favourites
    url = plugin.url_for('favourites')
    list_item = {'label': _('Watch Later'),
                 'url': url,
                 'icon': plugin.get_image('DefaultFavourites.png'),
                 'fanart': plugin.fanart,
                 'content_lookup': False,
                 }
    yield list_item

    # Purchases
    url = plugin.url_for('purchases')
    list_item = {'label': _('Purchases'),
                 'url': url,
                 # 'icon': plugin.get_image('DefaultFavourites.png'),
                 'icon': plugin.icon,
                 'fanart': plugin.fanart,
                 'content_lookup': False,
                 }
    yield list_item

    # Unfinished
    url = plugin.url_for('unfinished')
    list_item = {'label': _('Unfinished'),
                 'url': url,
                 # 'icon': plugin.get_image('DefaultFavourites.png'),
                 'icon': plugin.icon,
                 'fanart': plugin.fanart,
                 'content_lookup': False,
                 }
    yield list_item

    # Watch History
    url = plugin.url_for('watchhistory')
    list_item = {'label': _('Watch History'),
                 'url': url,
                 # 'icon': plugin.get_image('DefaultFavourites.png'),
                 'icon': plugin.icon,
                 'fanart': plugin.fanart,
                 'content_lookup': False,
                 }
    yield list_item

    # Search
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

    use_atl_names = plugin.params.get('atl')
    if use_atl_names is None \
      and plugin.get_setting('use_atl_names'):
        use_atl_names = plugin.get_setting('use_atl_names')
        plugin.params['atl'] = use_atl_names
    
    for item in data['list']:
        listitem = _get_listitem(item)
        yield listitem

    page_params = {}
    page_params.update(plugin.params)
    page_params['step'] = data['step']
    if use_atl_names:
        page_params['atl'] = use_atl_names

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


@plugin.route('/favourites')
def favourites():

    step = plugin.params.get('step', plugin.get_setting('step', False))
    step = int(step)
    start = plugin.params.get('from', '0')
    start = int(start)
    params = {'from': start,
              }

    try:
        favourites_info = api.user_favourites(step, **params)
        params = {'items': _list_favourites(favourites_info),
                  'total_items': favourites_info['count'],
                  'content': 'movies',
                  'category': _('Watch Later'),
                  'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
                  'update_listing': (start > 0),
                  }
    except api.APIException as e:
        plugin.notify_error(e.msg)
        params = {'items': [],
                  'succeeded': False,
                  }

    plugin.create_directory(**params)


@plugin.route('/watchhistory')
def watchhistory():

    step = plugin.params.get('step', plugin.get_setting('step', False))
    step = int(step)
    start = plugin.params.get('from', '0')
    start = int(start)
    params = {'from': start,
              }

    try:
        watchhistory_info = api.watchhistory(step, **params)
        params = {'items': _list_watchhistory(watchhistory_info),
                  'total_items': watchhistory_info['count'],
                  'content': 'movies',
                  'category': _('Watch History'),
                  'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
                  'update_listing': (start > 0),
                  }
    except api.APIException as e:
        plugin.notify_error(e.msg)
        params = {'items': [],
                  'succeeded': False,
                  }

    plugin.create_directory(**params)


@plugin.route('/unfinished')
def unfinished():

    step = plugin.params.get('step', plugin.get_setting('step', False))
    step = int(step)
    start = plugin.params.get('from', '0')
    start = int(start)
    params = {'from': start,
              }

    try:
        unfinished_info = api.unfinished(step, **params)
        params = {'items': _list_favourites(unfinished_info),
                  'total_items': unfinished_info['count'],
                  'content': 'movies',
                  'category': _('Unfinished'),
                  'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
                  'update_listing': (start > 0),
                  }
    except api.APIException as e:
        plugin.notify_error(e.msg)
        params = {'items': [],
                  'succeeded': False,
                  }

    plugin.create_directory(**params)


@plugin.route('/purchases')
def purchases():

    step = plugin.params.get('step', plugin.get_setting('step', False))
    step = int(step)
    start = plugin.params.get('from', '0')
    start = int(start)
    params = {'from': start,
              }

    try:
        purchases_info = api.purchases(step, **params)
        params = {'items': _list_favourites(purchases_info),
                  'total_items': purchases_info['count'],
                  'content': 'movies',
                  'category': _('Purchases'),
                  'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
                  'update_listing': (start > 0),
                  }
    except api.APIException as e:
        plugin.notify_error(e.msg)
        params = {'items': [],
                  'succeeded': False,
                  }

    plugin.create_directory(**params)


def _list_favourites(data):

    use_pages = True

    use_atl_names = plugin.params.get('atl')
    if use_atl_names is None \
      and plugin.get_setting('use_atl_names'):
        use_atl_names = plugin.get_setting('use_atl_names')
        plugin.params['atl'] = use_atl_names

    for item in data['list']:
        listitem = _get_listitem(item)
        yield listitem

    page_params = {}
    page_params.update(plugin.params)
    page_params['step'] = data['step']
    if use_atl_names:
        page_params['atl'] = use_atl_names

    if use_pages \
      and data['from'] >= data['step']:
        page_params['from'] = data['from'] - data['step']
        if page_params['from'] == 0:
            del page_params['from']

        url = plugin.url_for('favourites', **page_params)
        item_info = {'label': _('Previous page...'),
                     'url':   url}
        yield item_info

    if use_pages \
      and data['total'] >= data['from'] + data['step']:
        page_params['from'] = data['from'] + data['step']
        url = plugin.url_for('favourites', **page_params)
        item_info = {'label': _('Next page...'),
                     'url':   url}
        yield item_info


def _list_watchhistory(data):

    use_pages = True

    use_atl_names = plugin.params.get('atl')
    if use_atl_names is None \
      and plugin.get_setting('use_atl_names'):
        use_atl_names = plugin.get_setting('use_atl_names')
        plugin.params['atl'] = use_atl_names

    for item in data['list']:
        listitem = _get_listitem(item)
        yield listitem

    page_params = {}
    page_params.update(plugin.params)
    page_params['step'] = data['step']
    if use_atl_names:
        page_params['atl'] = use_atl_names

    if use_pages \
      and data['from'] >= data['step']:
        page_params['from'] = data['from'] - data['step']
        if page_params['from'] == 0:
            del page_params['from']

        url = plugin.url_for('watchhistory', **page_params)
        item_info = {'label': _('Previous page...'),
                     'url':   url}
        yield item_info

    if use_pages \
      and data['total'] >= data['from'] + data['step']:
        page_params['from'] = data['from'] + data['step']
        url = plugin.url_for('watchhistory', **page_params)
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
    use_atl_names = plugin.params.get('atl', False)

    try:
        season_info = api.videofromcompilation(compilation_id, season)

        if use_atl_names:
            sort_methods = xbmcplugin.SORT_METHOD_NONE
        else:
            sort_methods = xbmcplugin.SORT_METHOD_EPISODE
            
        params = {'items': _list_episodes(season_info),
                  'total_items': season_info['count'],
                  'content': 'episodes',
    #              'category': season_info['title'],
                  'sort_methods': sort_methods,
                  'cache_to_disk': True,
                  }
    except api.APIException as e:
        plugin.notify_error(e.msg)
        params = {'items': [],
                  'succeeded': False,
                  }

    plugin.create_directory(**params)


def _list_episodes(data):
    use_atl_names = plugin.params.get('atl', False)
    if use_atl_names:
        compilation_info = api.compilationinfo(data['compilation_id'])
    else:
        compilation_info = {}
    
    item = {'compilation_orig_title': compilation_info.get('orig_title', ''),
            }
    for _item in data['list']:
        item.update(_item)
        listitem = _get_listitem(item)
        yield listitem


def _get_listitem(item, _watch=False):
    properties = {}
    video_info_upd = {}
    orig_title = ''
    countries = _countries()

    use_atl_names = plugin.params.get('atl', False)
    ext_params = {}
    if use_atl_names:
        ext_params['atl'] = use_atl_names
    
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
            
            if use_atl_names:
                atl_name_parts = []
    
                if orig_title:
                    atl_name_parts.append(orig_title)
                else:
                    atl_name_parts.append(title)
                    
                if item['year'] > 0:
                    atl_name_parts.append(' ({0})'.format(item['year']))
                    
                title = ''.join(atl_name_parts)
            
            mediatype = 'movie'

            video_info_upd = {'duration': item['duration_minutes'] * 60,
                              }
        else:
            title = item['title']
            orig_title = item['orig_title']
            season = max(item.get('season', 0), 1)
            
            if use_atl_names:
                atl_name_parts = []
                if item.get('compilation_orig_title', ''):
                    atl_name_parts.append(item['compilation_orig_title'])
                else:
                    atl_name_parts.append(item['compilation_title'])
                    
                atl_name_parts.append('.s%02de%02d' % (season, item['episode']))

                if orig_title:
                    atl_name_parts.append('-')
                    atl_name_parts.append(orig_title)
                elif title:
                    atl_name_parts.append('-')
                    atl_name_parts.append(title)
                    
                title = ''.join(atl_name_parts)

            mediatype = 'episode'

            video_info_upd = {'duration': item['duration_minutes'] * 60,
                              'tvshowtitle': item['compilation_title'],
                              'episode': item['episode'],
                              'season': season,
                              'sortepisode': item['episode'],
                              'sortseason': season,
                              }

    elif item['object_type'] == 'compilation':
        if item['seasons_count'] == 0:
            url = plugin.url_for('compilation_season_short', compilation_id=item['id'], **ext_params)
        else:
            url = plugin.url_for('compilation', compilation_id=item['id'], **ext_params)
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
        url = plugin.url_for('compilation_season', compilation_id=item['id'], season=item['season'], **ext_params)
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
 
    if not _watch:
        if item['content_paid_type'] == 'SVOD':
            paid_shield = '[{0}]'.format(_('Subscription'))
        elif item['content_paid_type'] == 'EST':
            paid_shield = '[{0}]'.format(_('Purchase'))
        else:
            paid_shield = None
    
        if paid_shield is not None:
            title = '{0} {1}'.format(title, paid_shield)

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
        listitem = _get_listitem(video_info, True)

        videolinks = api.videolinks(video_id)
        path_MP4 = _get_video_path(videolinks, 'MP4')
        path_DASH = _get_video_path(videolinks, 'DASH-MDRM')
        if path_MP4 is not None:
            listitem['path'] = path_MP4['url']
        elif path_DASH is not None:
            # fix minimum kodi version
            new_kodi_versions = {
                'Windows': '18.0',
                'Linux': '18.0',
                'Darwin': '18.0'
            }            
            inputstreamhelper.config.WIDEVINE_MINIMUM_KODI_VERSION.update(new_kodi_versions)
            
            ia_helper = inputstreamhelper.Helper('mpd', drm='widevine')
            if ia_helper.check_inputstream():
                license_key = api.get_license_key(video_id, path_DASH['mdrm_asset_id'])
                properties = {'inputstream.adaptive.license_type': 'com.widevine.alpha',
                              'inputstream.adaptive.license_key': license_key + '|Content-Type=application/octet-stream&User-Agent=' + xbmc.getUserAgent() + '&Accept-Encoding=gzip&Connection=Keep-Alive|R{SSM}|',
                              'inputstream.adaptive.server_certificate': api.get_server_certificate(),
                              'inputstream.adaptive.manifest_type': 'mpd',
                              'inputstreamaddon': 'inputstream.adaptive',
                              }
                # listitem['mime'] = 'application/dash+xml'
                listitem['properties'] = properties
                listitem['path'] = path_DASH['url']  # api.get_link(path_DASH);
            
    except api.APIException as e:
        plugin.notify_error(e.msg)
        succeeded = False
        listitem = {}

    plugin.resolve_url(listitem, succeeded)


def _get_video_path(links, prefix):

    video_quality = plugin.get_setting('video_quality')

    quality_list = ['lo', 'hi', 'SHQ', 'HD720', 'HD1080']
    
    path = None
    for i, q in enumerate(quality_list):
        field = '{0}-{1}'.format(prefix, q)
        if (not path or video_quality >= i) and links.get(field) is not None:
            path = links[field]

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
                    'is_folder': False,
                    'is_playable': False,
                    'fanart': plugin.fanart})

    for item in history:
        listing.append({'label': item['keyword'],
                        'url': plugin.url_for('search', keyword=item['keyword']),
                        'icon': plugin.icon,
                        'is_folder': True,
                        'is_playable': False,
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
        safe_search = plugin.get_setting('safe_search')
        videos_info = api.search(keyword, safe_search)
        params = {'items': _list_search(videos_info),
                  # 'total_items': unfinished_info['count'],
                  'content': 'movies',
                  'category': '{0}/{1}'.format(_('Search'), keyword),
                  'sort_methods': {'sortMethod': xbmcplugin.SORT_METHOD_NONE, 'label2Mask': '%Y / %O'},
                  }
        plugin.create_directory(**params)


@plugin.route('/login')
def login():
    _login = _get_keyboard_text('', _('E-mail/Phone'))
    if not _login:
        return

    dialog = xbmcgui.Dialog()

    try:
        validate_result = api.user_validate(_login)
    except api.APIException as e:
        dialog.ok(plugin.name, e.msg)
        return
    
    if validate_result['action'] == 'login':
        if validate_result['what'] == 'email':
            _password = _get_keyboard_text('', _('Password'), True)
            if not _password:
                return
            try:
                login_result = api.user_login_ivi(_login, _password)
            except api.APIException as e:
                dialog.ok(plugin.name, e.msg)
                return
        elif validate_result['what'] == 'phone':
            try:
                register_result = api.user_register_phone(_login)
            except api.APIException as e:
                dialog.ok(plugin.name, e.msg)
                return
            if not register_result['success']:
                return
            _code = _get_keyboard_text('', _('SMS code'))
            if not _code:
                return
            try:
                login_result = api.user_login_phone(_login, _code)
            except api.APIException as e:
                dialog.ok(plugin.name, e.msg)
                return

        api.set_prop('session', login_result['session'])
        merge_result = api.user_merge(plugin.get_setting('session'))
        if merge_result == 'ok':
            user_fields = get_user_fields(login_result)
            user_fields['user_login'] = _login
            user_fields['session'] = login_result['session']
            plugin.set_settings(user_fields)

        dialog.ok(plugin.name, _('You have successfully logged in'))
    elif validate_result['action'] == 'register':
        dialog.ok(plugin.name, _('Login not registered'))


def _get_keyboard_text(line='', heading='', hidden=False):            
    kbd = xbmc.Keyboard(line, heading, hidden)
    kbd.doModal()
    if kbd.isConfirmed():
        return kbd.getText()


def get_user_fields(user_info=None):
    user_info = user_info or {}

    fields = {'user_login': user_info.get('login') or '',
              'user_name': '{0} {1}'.format(user_info.get('firstname') or '', user_info.get('lastname') or '').strip(),
              'user_id': user_info.get('id') or '',
              'user_phone': user_info.get('msisdn') or '',
              'user_email': user_info.get('email') or '',
              'user_gender': user_info.get('gender') or 0,
              'user_birthday': (user_info.get('birthday') or '')[0:4],
              }

    return fields


@plugin.route('/logout')
def logout():
    try:
        logout_result = api.user_logout()
    except api.APIException as e:
        pass

    user_fields = get_user_fields()
    
    user_fields['session'] = ''
    user_fields['user_ab_bucket'] = ''
    plugin.set_settings(user_fields)

    dialog = xbmcgui.Dialog()
    dialog.ok(plugin.name, _('You have successfully logged out'))
    
    
def _list_search(data):

    for item in data['list']:
        listitem = _get_listitem(item)
        yield listitem


def _init_api():
    global api
    global country

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
            session_info = api.user_register()
            session = session_info['session']
            # user_ab_bucket = session_info['user_ab_bucket']

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
        country = geo_info['country_code']

        app_info = _api_appinfo()
        if app_info['subsite_id'] != subsite_id:
            plugin.set_setting('subsite_id', app_info['subsite_id'])
            api.set_prop('subsite_id', app_info['subsite_id'])

        if not plugin.get_setting('user_id'):
            user_info = api.user_info()
            
            user_fields = get_user_fields(user_info)
            plugin.set_settings(user_fields)
 
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
