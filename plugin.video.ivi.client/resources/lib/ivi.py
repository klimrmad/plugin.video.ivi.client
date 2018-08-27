# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import json
import random

from future.utils import python_2_unicode_compatible, iteritems
import requests
from base64 import b64encode
from urllib.parse import urlencode

from .blowfish import Blowfish


@python_2_unicode_compatible
class IVI(object):

    _api_url = 'https://api.ivi.ru/'

    @python_2_unicode_compatible
    class APIException(Exception):

        def __init__(self, msg):
            self.msg = msg

        def __str__(self):
            return self.msg

    def __init__(self, app_version='2277'):
        self._app_version = app_version
        self._uid = ''
        self._user_ab_bucket = ''
        self._subsite_id = 959
        self._session = ''
        self._key = ''
        self._key1 = ''
        self._key2 = ''

        self._headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
                         'Accept-Encoding': 'gzip, deflate, br',
                         'DNT': '1',
                         'Connection': 'keep-alive',
                         }

    def __str__(self):
        return 'IVI : app_version-{0}; subsite_id-{1}'.format(self._app_version, self._subsite_id)

    def set_prop(self, prop, value):
        if prop == 'app_version':
            self._app_version = value
        elif prop == 'uid':
            self._uid = value
        elif prop == 'user_ab_bucket':
            self._user_ab_bucket = value
        elif prop == 'subsite_id':
            self._subsite_id = value
        elif prop == 'session':
            self._session = value
        elif prop == 'key':
            self._key = value.decode('hex')
        elif prop == 'key1':
            self._key1 = value.decode('hex')
        elif prop == 'key2':
            self._key2 = value.decode('hex')

    @staticmethod
    def get_uid():
        uid = str((1E6 * random.random() + random.random()))[0:15]
        return uid

    def get_session(self, url=None):
        url = url or 'https://www.ivi.ru/'

        try:
            r = requests.head(url, headers=self._headers)
            r.raise_for_status()

        except requests.ConnectionError:
            raise self.APIException('Connection error')
        except requests.HTTPError as e:
            raise self.APIException(str(e))

        if r.status_code == 302:
            result = self.get_session(r.headers['location'])
        else:
            result = {'session': r.cookies['sessivi'],
                      'user_ab_bucket': r.cookies['user_ab_bucket'],
                      }

        return result

    def get_server_certificate(self):
        url = 'https://w.ivi.ru/certificate/'

        try:
            r = requests.get(url, headers=self._headers)
            r.raise_for_status()

        except requests.ConnectionError:
            raise self.APIException('Connection error')
        except requests.HTTPError as e:
            raise self.APIException(str(e))

        result = b64encode(r.content)

        return result

    def get_license_key(self, content_id, mdrm_asset_id):
        url = 'https://w.ivi.ru/proxy/'

        license_keys = {'content_id': content_id,
                        'asset': mdrm_asset_id,
                        'app_version': self._app_version,
                        'session': self._session,
                        }
    
        return '{0}?{1}'.format(url, urlencode(license_keys, doseq=True))
 
    def _get_sign(self, text):
        cipher = Blowfish(self._key)
        cipher.initCBC()

        data = bytes(text)

        offset = 0
        data_len = len(data)
        while (offset + 8 < data_len):
            cipher.encryptCBC(data[offset : offset + 8])
            offset += 8

        buffer = b''
        if (offset != data_len):
            buffer = data[offset : ]

        sub_key = self._key1
        if (len(buffer) < 8):
            buffer += b'\x80';
            while (len(buffer) < 8):
                buffer += b'\x00'
            sub_key = self._key2

        new_buffer = b''
        for i in range(8):
            new_buffer += chr(ord(buffer[i]) ^ ord(sub_key[i]))

        sign = cipher.encryptCBC(new_buffer)
        return sign.encode('hex')

    def _http_request(self, url_path, params=None, rtype='GET', **kwqrgs):
        params = params or {}
        params['app_version'] = self._app_version

        url = self._api_url + url_path
        try:
            if rtype == 'GET':
                r = requests.get(url, params, headers=self._headers, **kwqrgs)
            elif rtype == 'POST':
                r = requests.post(url, params, headers=self._headers, **kwqrgs)
            # print(r.url)
            r.raise_for_status()
        except requests.ConnectionError:
            raise self.APIException('Connection error')
        except requests.HTTPError as e:
            raise self.APIException(str(e))

        return r

    def _extract_json(self, r):
        try:
            j = r.json()
        except ValueError as err:
            raise APIException(err)

        if isinstance(j, dict) \
          and j.get('error') is not None:
            if j['error'].get('user_message') is not None:
                raise self.APIException(j['error']['user_message'])
            else:
                raise self.APIException(j['error']['message'])
        return j

    def appversioninfo(self):
        url = 'mobileapi/appversioninfo/v5/'

        u_params = {}
        if self._uid:
            u_params['uid'] = self._uid

        r = self._http_request(url, u_params)
        j = self._extract_json(r)
        result = j['result']

        return {'last_version_id': result['last_version_id'],
                'application_id': result['application_id'],
                'description': result['description'],
                'subsite_id': result['subsite_id'],
                'subsite_title': result['subsite_title'],
                'id': result['id'],
                }

    def geocheck(self):
        url = 'mobileapi/geocheck/whoami/v6/'

        u_params = {}
        if self._user_ab_bucket:
            u_params['user_ab_bucket'] = self._user_ab_bucket

        r = self._http_request(url, u_params)
        j = self._extract_json(r)
        result = j['result']

        return {'country_code': result['country_code'],
                'country_name': result['country_name'],
                'timestamp': result['timestamp'],
                'country_place_id': result['country_place_id'],
                'user_ab_bucket': result['user_ab_bucket'],
                'actual_app_version': result['actual_app_version'],
                }

    def categories(self):
        url = 'mobileapi/categories/v5/'

        r = self._http_request(url)
        j = self._extract_json(r)

        for category in j['result']:
            genres = {}
            for genre in category['genres']:
                genres[genre['hru']] = {'title': genre['title'],
                                        'id': int(genre['id']),
                                        }

            yield {'id': category['id'],
                   'title': category['title'],
                   'hru': category['hru'],
                   'description': category['description'],
                   'genres': genres,
                   }

    def localizations(self):
        url = 'mobileapi/localizations/v5'

        r = self._http_request(url)
        j = self._extract_json(r)

        for _id, localization in iteritems(j['result']):
            yield {'id': _id,
                   'title': localization,
                   }

    def countries(self):
        url = 'mobileapi/countries/v5/'

        r = self._http_request(url)
        j = self._extract_json(r)

        for _id, country in iteritems(j['result']):
            yield {'id': _id,
                   'title': country,
                   }

    def catalogue(self, category_id, step=20, **kwargs):
        params = kwargs or {}
        url = 'mobileapi/catalogue/v5/'

        fields = ['allow_download', 'country', 'description', 'years', 'total_contents', 'artists', 'orig_title', 'seasons_count',
                  'duration_minutes', 'fake', 'genres', 'has_creators', 'id', 'imdb_rating', 'ivi_pseudo_release_date', 'release_date',
                  'ivi_rating_10', 'ivi_release_date', 'kind', 'kp_rating', 'poster_originals.path', 'restrict', 'subsites_availability',
                  'synopsis', 'thumb_originals.path', 'title', 'unavailable_on_current_subsite', 'watch_time', 'year',
                  'additional_data.additional_data_id-data_type-duration-preview-title', 'count', 'object_type',
                  'promo_images.content_format-url', 'categories', 'available_in_countries', 'content_paid_type']

        start = params.get('from', 0)
        sort = params.get('sort', 'new')
        u_params = {'from': start,
                    'to': start + step - 1,
                    # 'paid_type': 'EST',
                    'sort': sort,
                    'category': category_id,
                    'fields': ','.join(fields)}
        r = self._http_request(url, u_params)
        j = self._extract_json(r)

        result = {'count': len(j['result']),
                  'total': j['count'],
                  'from': start,
                  'step': step,
                  'list': self._catalogue_list(j['result']),
                  }

        return result

    @staticmethod
    def _make_item(item):

        result = {'restrict': item['restrict'],
                 'artists': item['artists'],
                 'id': item['id'],
                 'genres': item['genres'],
                 'title': item['title'],
                 'orig_title': item['orig_title'],
                 'kind': item['kind'],
                 'object_type': item['object_type'],
                 'description': item['description'],
                 'synopsis': item['synopsis'],
                 'country': item['country'],
                 'release_date': item['release_date'],
                 'imdb_rating': item.get('imdb_rating', ''),
                 'kp_rating': item.get('kp_rating', ''),
                 'ivi_rating': item.get('ivi_rating_10', ''),
                 'categories': item['categories'],
                 'content_paid_type': item.get('content_paid_type', ''),
                 'available_in_countries': item.get('available_in_countries', []),
                 }
        if item.get('poster_originals') is not None \
          and item['poster_originals']:
            result['poster'] = item['poster_originals'][0]['path']
        if item.get('thumb_originals') is not None \
          and item['thumb_originals']:
            result['thumb'] = item['thumb_originals'][0]['path']
        if item.get('promo_images') is not None \
          and item['promo_images']:
            result['promo'] = item['promo_images'][0]['url']

        if item['object_type'] == 'video':
            result.update({'year': item.get('year'),
                           'duration_minutes': item['duration_minutes'],
                           })
            if item.get('compilation_title') is not None:
                result.update({'episode': item['episode'],
                               'compilation': item['compilation'],
                               'compilation_title': item['compilation_title'],
                               })
            if item.get('season'):
                result['season'] = item['season']

        elif item['object_type'] == 'compilation':
            result.update({'year': item['years'][0] if item['years'] else None,
                           'total_contents': item['total_contents'],
                           'seasons_count': item['seasons_count'],
                          })
            if item.get('seasons') is not None:
                result.update({'seasons': item['seasons'],
                               'seasons_content_total': item['seasons_content_total'],
                               'seasons_description': item.get('seasons_description', {}),
                              })
        return result

    @classmethod
    def _catalogue_list(cls, items):
        for item in items:
            yield cls._make_item(item)

    @classmethod
    def _purchases_list(cls, items):
        for item in items:
            if item['object_type'] == 'content':
                yield cls._make_item(item['object_info'])

    def compilationinfo(self, compilation_id):
        url = 'mobileapi/compilationinfo/v5/'

        fields = ['country', 'description', 'duration_minutes', 'fake', 'genres', 'has_upcoming_episodes',
                  'hd_available', 'id', 'imdb_rating', 'ivi_rating_10', 'release_date', 'kind', 'kp_rating', 'poster_originals.path',
                  'restrict', 'season', 'seasons', 'seasons_content_total', 'seasons_count', 'subtitles',
                  'synopsis', 'thumb_originals.path', 'title', 'unavailable_on_current_subsite', 'watch_time', 'year', 'years',
                  'additional_data.additional_data_id-data_type-duration-preview-title', 'background.path-type',
                  'branding.files.content_format-url', 'branding.link-px_audit', 'ivi_release_info.date_interval_max-date_interval_min',
                  'promo_images.content_format-url', 'artists', 'orig_title', 'object_type', 'total_contents', 'seasons_count',
                  'seasons_description', 'categories']

        u_params = {'id': compilation_id,
                    'fields': ','.join(fields)}
        r = self._http_request(url, u_params)
        j = self._extract_json(r)

        return self._make_item(j['result'])

    def videofromcompilation(self, compilation_id, season=None):
        url = 'mobileapi/videofromcompilation/v5/'

        fields = ['categories', 'compilation', 'compilation_title', 'country', 'description', 'content_paid_type',
                  'duration_minutes', 'episode', 'fake', 'genres', 'has_creators', 'id', 'imdb_rating', 'ivi_rating_10',
                  'ivi_release_date', 'kind', 'kp_rating', 'poster_originals.path', 'restrict', 'season', 'synopsis',
                  'thumb_originals.path', 'title', 'year', 'additional_data.additional_data_id-data_type-duration-preview-title',
                  'promo_images.content_format-url', 'artists', 'orig_title', 'object_type', 'release_date', 'available_in_countries']

        start = 0
        step = 100

        items = []

        u_params = {'id': compilation_id,
                    'from': start,
                    'to': start + step - 1,
                    'fields': ','.join(fields)}
        if season is not None:
            u_params['season'] = season

        while True:
            r = self._http_request(url, u_params)
            j = self._extract_json(r)
            items.extend(j['result'])
            if len(j['result']) == step:
                u_params['from'] += step
                u_params['to'] += step

            else:
                break

        result = {'count': len(items),
                  'compilation_id': compilation_id,
                  'list': self._catalogue_list(items),
                  }
        return result

    def videoinfo(self, video_id):
        url = 'mobileapi/videoinfo/v5/'

        fields = ['categories', 'compilation', 'compilation_title', 'content_paid_type', 'country', 'description',
                  'duration_minutes', 'episode', 'fake', 'genres', 'has_creators', 'id', 'imdb_rating', 'ivi_rating_10',
                  'ivi_release_date', 'kind', 'kp_rating', 'poster_originals.path', 'restrict', 'season', 'synopsis',
                  'thumb_originals.path', 'title', 'year', 'additional_data.additional_data_id-data_type-duration-preview-title',
                  'promo_images.content_format-url', 'artists', 'orig_title', 'object_type', 'release_date', 'available_in_countries']

        u_params = {'id': video_id,
                    'fields': ','.join(fields)}

        r = self._http_request(url, u_params)
        j = self._extract_json(r)

        return self._make_item(j['result'])

    def videolinks(self, video_id):
        url = 'light/'

        u_json = {'method':'da.timestamp.get',
                  'params':[]
                  }

        r = self._http_request(url, json=u_json)
        j = self._extract_json(r)

        u_json = {'method':'da.content.get',
                  'params':[video_id,
                            {'app_version': self._app_version,
                             'session': self._session,
                             'site': 's{0}'.format(self._subsite_id),
                             'uid': self._uid,
                             '_url': 'https://www.ivi.ru/watch/{0}'.format(video_id),
                             'adblock': 0,
                             'user_ab_bucket': self._user_ab_bucket,
                             }]
                  }

        data = json.dumps(u_json)
        u_params = {'ts': j['result'],
                    'sign': self._get_sign(j['result'] + data),
                    }

        r = self._http_request(url, u_params, data=data)
        j = self._extract_json(r)

        result = {}
        for _file in j['result']['files']:
            result[_file['content_format']] = _file

        return result

    def search(self, keyword, safe_search=False):

        url = 'mobileapi/search/common/'

        u_params = {'query': keyword,
                    'from': 0,
                    'to': 99,
#                    'paid_type': 'AVOD',
                    'withpreorderable': 0,
                    }
        if safe_search:
            u_params['age'] = 16

        r = self._http_request(url, params=u_params)
        j = self._extract_json(r)

        items = []
        for item in j:
            if item['object_type'] in ['video', 'compilation']:
                items.append(item)

        result = {'count': len(items),
                  'list': self._catalogue_list(items),
                  }

        return result

    def user_validate(self, value):
        
        url = 'mobileapi/user/validate/v5/'

        u_params = {'value': value,
                    'user_ab_bucket': self._user_ab_bucket,
                    'session': self._session,
                    }

        r = self._http_request(url, params=u_params, rtype='POST')
        j = self._extract_json(r)

        return j['result']

    def user_login_ivi(self, login, password):
        
        url = 'mobileapi/user/login/ivi/v5/'
        
        u_params = {'email': login,
                    'password': password,
                    'session': self._session,
                    }

        r = self._http_request(url, params=u_params, rtype='POST')
        j = self._extract_json(r)

        return j['result']

    def user_login_phone(self, phone, code):
        
        url = 'mobileapi/user/login/phone/v5/'
        
        u_params = {'phone': phone,
                    'code': code,
                    'session': self._session,
                    }

        r = self._http_request(url, params=u_params, rtype='POST')
        j = self._extract_json(r)

        return j['result']

    def user_merge(self, rightsession):
        
        url = '/mobileapi/user/merge/v5/'
        
        u_params = {'rightsession': rightsession,
                    'session': self._session,
                    }

        r = self._http_request(url, params=u_params, rtype='POST')
        j = self._extract_json(r)

        return j['result']
        
    def user_info(self):
        
        url = 'mobileapi/user/info/v5/'
        
        u_params = {'session': self._session,
                    }

        r = self._http_request(url, params=u_params)
        j = self._extract_json(r)

        return j['result']

    def user_logout(self):
        
        url = 'mobileapi/user/logout/v5/'
        
        u_params = {'session': self._session,
                    }

        r = self._http_request(url, params=u_params, rtype='POST')
        j = self._extract_json(r)

        return j['result']

    def user_register(self, storageless=True):
        
        if storageless:
            url = 'mobileapi/user/register/storageless/v5/'
        
        r = self._http_request(url, rtype='POST')
        j = self._extract_json(r)

        return j['result']

    def user_register_phone(self, phone):
        
        url = 'mobileapi/user/register/phone/v6/'
  
        u_params = {'phone': phone,
                    'session': self._session,
                    }

        r = self._http_request(url, params=u_params, rtype='POST')
        j = self._extract_json(r)

        return j['result']

    def user_favourites_count(self):
        
        url = 'mobileapi/user/favourites/v5/count'
  
        u_params = {'withunavailable': 1,
                    'session': self._session,
                    }

        r = self._http_request(url, params=u_params)
        j = self._extract_json(r)

        return j['result']

    def user_favourites(self, step=20, **kwargs):
        params = kwargs or {}
        url = 'mobileapi/user/favourites/v5/'

        start = params.get('from', 0)
        u_params = {'from': start,
                    'to': start + step - 1,
                    'withunavailable': 0,
                    'user_ab_bucket': self._user_ab_bucket,
                    'session': self._session,
                    }

        r = self._http_request(url, params=u_params)
        j = self._extract_json(r)

        result = {'count': len(j['result']),
                  'total': self.user_favourites_count(),
                  'from': start,
                  'step': step,
                  'list': self._catalogue_list(j['result']),
                  }

        return result

    def watchhistory(self, step=20, **kwargs):
        params = kwargs or {}
        url = 'mobileapi/watchhistory/v5/'

        start = params.get('from', 0)
        u_params = {'from': start,
                    'to': start + step - 1,
                    'user_ab_bucket': self._user_ab_bucket,
                    'session': self._session,
                    }

        r = self._http_request(url, params=u_params)
        j = self._extract_json(r)

        if params.get('count_list', False):
            result = {'count': len(j['result']),
                      'from': start,
                      'step': step,
                      }
        else:
            params['from'] = start + step
            params['count_list'] = True
            
            next_list = self.watchhistory(step, **params)

            result = {'count': len(j['result']),
                      'total': len(j['result']) + start + next_list['count'],
                      'from': start,
                      'step': step,
                      'list': self._catalogue_list(j['result']),
                      }

        return result

    def unfinished(self, step=20, **kwargs):
        params = kwargs or {}
        url = 'mobileapi/unfinished/video/v5/'

        start = params.get('from', 0)
        u_params = {'from': start,
                    'to': start + step - 1,
                    'user_ab_bucket': self._user_ab_bucket,
                    'session': self._session,
                    }

        r = self._http_request(url, params=u_params)
        j = self._extract_json(r)

        if params.get('count_list', False):
            result = {'count': len(j['result']),
                      'from': start,
                      'step': step,
                      }
        else:
            params['from'] = start + step
            params['count_list'] = True
            
            next_list = self.unfinished(step, **params)

            result = {'count': len(j['result']),
                      'total': len(j['result']) + start + next_list['count'],
                      'from': start,
                      'step': step,
                      'list': self._catalogue_list(j['result']),
                      }

        return result

    def purchases(self, step=20, **kwargs):
        params = kwargs or {}
        url = 'mobileapi/billing/v1/purchases/'

        start = params.get('from', 0)
        u_params = {'user_ab_bucket': self._user_ab_bucket,
                    'session': self._session,
                    }

        r = self._http_request(url, params=u_params)
        j = self._extract_json(r)

        result = {'count': len(j['result']),
                  'total': len(j['result']),
                  'from': start,
                  'step': step,
                  'list': self._purchases_list(j['result']),
                  }

        return result

    @staticmethod
    def get_age_restricted_rating(min_age, rating_type):
        if min_age == 0:
            rars = '0+'
            mpaa = 'G'
        elif min_age == 6:
            rars = '6+'
            mpaa = 'PG'
        elif min_age == 12:
            rars = '12+'
            mpaa = 'PG-13'
        elif min_age == 16:
            rars = '16+'
            mpaa = 'R'
        elif min_age == 18:
            rars = '18+'
            mpaa = 'NC-17'
        else:
            rars = ''
            mpaa = ''

        result = {'rars': rars,
                  'mpaa': mpaa,
                  }

        return result.get(rating_type, '')
