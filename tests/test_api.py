import glob
import json
import os
import urllib.parse
import sys

import pytest

import pygeonlp.api as geonlp_api
from pygeonlp_webapi.app import app
from pygeonlp_webapi.config.default import config

"""
Unit tests for pygeonlp_webapi.

run `pytest` to do all tests.
run `pytest -k <funcname>` to do the matched tests.
"""

gdal_not_installed = False
try:
    import gdal
except ModuleNotFoundErrlr:
    gdal_not_installed = True


@pytest.fixture(scope="session", autouse=True)
def createTempDatabase(tmp_path_factory):
    """
    Create temporary geonlp database for the tests.
    """
    if False:
        # Setup test database in a temporary directory
        db_dir = str(tmp_path_factory.mktemp('db'))
        geonlp_api.setup_basic_database(db_dir=db_dir)
        geonlp_api.init(db_dir=db_dir,
                        **(config.GEONLP_API_OPTIONS))
    else:
        # or, use default database under GEONLP_DB_DIR
        pass


@pytest.fixture(scope="function", autouse=True)
def setup():
    app.config['TESTING'] = True


@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            yield client


"""
Tools
"""


def print_response(rv):
    print("code:{}, data:'{}'".format(rv.status_code, rv.data),
          file=sys.stderr)


def validate_jsonrpc(client, query, expected):
    """
    Send query and compare the result with expected.

    Parameters
    ----------
    client: client fixture
    query: str
        The query string to POST to the server
    expected: any
        The value expected as a result.
        The JSON decoded value stored in the 'result'
        field of the response is used.

        When '*' is passed as 'expected', any response will pass.

    Return
    ------
    any
        The JSON decoded value stored in the 'result'
        field of the response.
    """
    headers = {"Content-Type": "application/json"}
    rv = client.post('/api', data=query, headers=headers)
    assert rv.status_code == 200
    response_json = json.loads(rv.data)
    result = response_json['result']
    if expected != '*':
        assert result == expected

    return result


def validate_jsonrpc_error(client, query, expected_code):
    """
    Send query and compare the status code with expected_code.

    Parameters
    ----------
    client: client fixture
    query: str
        The query string to POST to the server
    expected_code: int
        The expected status_code.
    """
    headers = {"Content-Type": "application/json"}
    rv = client.post('/api', data=query, headers=headers)
    assert rv.status_code == expected_code


class TestBasicApi:
    """
    基本的な API のテスト
    """

    def test_parse(self, client):
        """
        Test ``geonlp.parse`` API.
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {'sentence': 'NIIは神保町駅から徒歩7分です。'},
            'id': 'test_parse',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 形態素解析のチェック
        words = 'NII/は/神保町駅/から/徒歩/7/分/です/。'.split('/')
        for pos, feature in enumerate(features):
            prop = feature['properties']
            assert prop['surface'] == words[pos]  # 表記が一致

            if prop['surface'] == '神保町駅':
                assert prop['node_type'] == 'GEOWORD'
            else:
                assert prop['node_type'] == 'NORMAL'

    def test_parse_geocoding(self, client):
        """
        Test ``geonlp.parse`` API using geocoding.
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': 'NIIは千代田区一ツ橋2-1-2にあります。',
                'options': {'geocoding': 'true'}
            },
            'id': 'test_parse_geocoding',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 形態素解析のチェック
        words = 'NII/は/千代田区一ツ橋2-1-/2/に/あり/ます/。'.split('/')
        for pos, feature in enumerate(features):
            prop = feature['properties']
            assert prop['surface'] == words[pos]  # 表記が一致

            if prop['surface'] == '千代田区一ツ橋2-1-':
                assert prop['node_type'] == 'ADDRESS'
            else:
                assert prop['node_type'] == 'NORMAL'

    def test_parseStructured(self, client):
        """
        Test ``geonlp.parseStructured`` API.
        """
        query = json.dumps({
            'method': 'geonlp.parseStructured',
            'params': {
                'sentence_list': [
                    'NIIは神保町駅から徒歩7分です。',
                    '千代田区一ツ橋2-1-2にあります。',
                    '竹橋駅も近いです。', ]
            },
            'id': 'test_parseStructured',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 形態素解析のチェック
        words = 'NII/は/神保町駅/から/徒歩/7/分/です/。'.split('/') +\
            '千代田区/一ツ橋/2/-/1/-/2/に/あり/ます/。'.split('/') +\
            '竹橋駅/も/近い/です/。'.split('/')
        for pos, feature in enumerate(features):
            prop = feature['properties']
            assert prop['surface'] == words[pos]  # 表記が一致

            if prop['surface'] in ('神保町駅', '千代田区', '竹橋駅'):
                assert prop['node_type'] == 'GEOWORD'
            else:
                assert prop['node_type'] == 'NORMAL'

    def test_search(self, client):
        """
        Test ``geonlp.search`` API.
        """
        query = json.dumps({
            'method': 'geonlp.search',
            'params': {'key': '国会議事堂前'},
            'id': 'test_search',
        })
        expected = {
            'QUy2yP': {
                'body': '国会議事堂前', 'dictionary_id': 3,
                'entry_id': '1b5cc77fc2c83713a6750642f373d01f',
                'geolod_id': 'QUy2yP',
                'hypernym': ['東京地下鉄', '9号線千代田線'],
                'institution_type': '民営鉄道',
                'latitude': '35.673543333333335',
                'longitude': '139.74305333333334',
                'ne_class': '鉄道施設/鉄道駅',
                'railway_class': '普通鉄道',
                'suffix': ['駅', ''],
                'dictionary_identifier': 'geonlp:ksj-station-N02-2019'
            },
            'fuquyv': {
                'body': '国会議事堂前', 'dictionary_id': 3,
                'entry_id': 'e630bf128884455c4994e0ac5ca49b8d',
                'geolod_id': 'fuquyv',
                'hypernym': ['東京地下鉄', '4号線丸ノ内線'],
                'institution_type': '民営鉄道',
                'latitude': '35.674845',
                'longitude': '139.74534166666666',
                'ne_class': '鉄道施設/鉄道駅',
                'railway_class': '普通鉄道',
                'suffix': ['駅', ''],
                'dictionary_identifier': 'geonlp:ksj-station-N02-2019'
            }
        }
        validate_jsonrpc(client, query, expected)

    def test_getGeoInfo_id(self, client):
        """
        Test ``geonlp.getGeoInfo`` API with single geolod_id.
        """
        query = json.dumps({
            'method': 'geonlp.getGeoInfo',
            'params': {'idlist': ['fuquyv']},
            'id': 'test_getGeoInfo_id',
        })
        expected = {'fuquyv': {
            'body': '国会議事堂前', 'dictionary_id': 3,
            'entry_id': 'e630bf128884455c4994e0ac5ca49b8d',
            'geolod_id': 'fuquyv',
            'hypernym': [
                '東京地下鉄', '4号線丸ノ内線'
            ], 'institution_type': '民営鉄道',
            'latitude': '35.674845', 'longitude': '139.74534166666666',
            'ne_class': '鉄道施設/鉄道駅', 'railway_class': '普通鉄道',
            'suffix': ['駅', ''],
            'dictionary_identifier': 'geonlp:ksj-station-N02-2019'
        }}
        validate_jsonrpc(client, query, expected)

    def test_getGeoInfo_idlist(self, client):
        """
        Test ``geonlp.getGeoInfo`` API with multiple geolod_id.
        """
        query = json.dumps({
            'method': 'geonlp.getGeoInfo',
            'params': {'idlist': ['fuquyv', 'QUy2yP']},
            'id': 'test_getGeoInfo_idlist',
        })
        expected = {
            'QUy2yP': {
                'body': '国会議事堂前', 'dictionary_id': 3,
                'entry_id': '1b5cc77fc2c83713a6750642f373d01f',
                'geolod_id': 'QUy2yP',
                'hypernym': ['東京地下鉄', '9号線千代田線'],
                'institution_type': '民営鉄道',
                'latitude': '35.673543333333335',
                'longitude': '139.74305333333334',
                'ne_class': '鉄道施設/鉄道駅',
                'railway_class': '普通鉄道',
                'suffix': ['駅', ''],
                'dictionary_identifier': 'geonlp:ksj-station-N02-2019'
            },
            'fuquyv': {
                'body': '国会議事堂前', 'dictionary_id': 3,
                'entry_id': 'e630bf128884455c4994e0ac5ca49b8d',
                'geolod_id': 'fuquyv',
                'hypernym': ['東京地下鉄', '4号線丸ノ内線'],
                'institution_type': '民営鉄道',
                'latitude': '35.674845',
                'longitude': '139.74534166666666',
                'ne_class': '鉄道施設/鉄道駅',
                'railway_class': '普通鉄道',
                'suffix': ['駅', ''],
                'dictionary_identifier': 'geonlp:ksj-station-N02-2019'
            }
        }
        validate_jsonrpc(client, query, expected)

    def test_getGeoInfo_nocandidate(self, client):
        """
        Test ``geonlp.getGeoInfo`` API with invalid geolod_id.
        """
        query = json.dumps({
            'method': 'geonlp.getGeoInfo',
            'params': {'idlist': ['aaaaaa']},
            'id': 'test_getGeoInfo_nocandidate',
        })
        expected = {'aaaaaa': None}
        validate_jsonrpc(client, query, expected)

    def test_getDictionaries(self, client):
        """
        Test ``geonlp.getDictionaries`` API.
        """
        query = json.dumps({
            'method': 'geonlp.getDictionaries',
            'params': {},
            'id': 'test_getDictionaries',
        })
        expected = ['geonlp:geoshape-city',
                    'geonlp:geoshape-pref',
                    'geonlp:ksj-station-N02-2019']
        validate_jsonrpc(client, query, expected)

    def test_getDictionaryInfo(self, client):
        """
        Test ``geonlp.getDictionaryInfo`` API.
        """
        query = json.dumps({
            'method': 'geonlp.getDictionaryInfo',
            'params': {'identifier': 'geonlp:ksj-station-N02-2019'},
            'id': 'test_getDictionaryInfo',
        })
        expected = '{"@context": "https://schema.org/", "@type": "Dataset", "alternateName": "", "creator": [{"@type": "Organization", "name": "株式会社情報試作室", "sameAs": "https://www.info-proto.com/"}], "dateModified": "2019-12-31T00:00:00+09:00", "description": "国土数値情報「鉄道データ（令和元年度）N02-19」（https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-v2_3.html）から作成した、日本の鉄道駅（地下鉄を含む）の辞書です。hypernymには運営者名と路線名を記載しています。「都営」ではなく「東京都」のようになっていますので注意してください。自由フィールドとして、railway_typeに「鉄道区分」、institution_typeに「事業者種別」を含みます。", "distribution": [{"@type": "DataDownload", "contentUrl": "https://www.info-proto.com/static/ksj-station-N02-2019.csv", "encodingFormat": "text/csv"}], "identifier": ["geonlp:ksj-station-N02-2019"], "isBasedOn": {"@type": "CreativeWork", "name": "鉄道データ（令和元年度）N02-19", "url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-v2_3.html"}, "keywords": ["GeoNLP", "地名辞書", "鉄道", "駅"], "license": "https://nlftp.mlit.go.jp/ksj/other/agreement.html", "name": "日本の鉄道駅（2019年）", "size": "10311", "spatialCoverage": {"@type": "Place", "geo": {"@type": "GeoShape", "box": "26.193265 127.652285 45.4161633333333 145.59723"}}, "temporalCoverage": "../..", "url": "https://www.info-proto.com/static/ksj-station-N02-2019.html"}'
        validate_jsonrpc(client, query, expected)

    def test_getDictionaryInfo_nocandidate(self, client):
        """
        Test ``geonlp.getDictionaryInfo`` API with invalid identifier.
        """
        query = json.dumps({
            'method': 'geonlp.getDictionaryInfo',
            'params': {'identifier': 'geonlp:abcdef'},
            'id': 'test_getDictionaryInfo_nocandidate',
        })
        expected = None
        validate_jsonrpc(client, query, expected)

    def test_addressGeocoding(self, client):
        """
        Test ``geonlp.addressGeocoding`` API.
        """
        query = json.dumps({
            'method': 'geonlp.addressGeocoding',
            'params': {'address': '千代田区一ツ橋2-1-2'},
            'id': 'test_addressGeocoding',
        })
        expected = {
            'candidates': [{
                'fullname': ['東京都', '千代田区', '一ツ橋', '二丁目', '1番'],
                'id': 11460296, 'level': 7, 'name': '1番', 'note': None,
                'x': 139.758148, 'y': 35.692332}],
            'matched': '千代田区一ツ橋2-1-'
        }
        validate_jsonrpc(client, query, expected)


class TestParseOptions:
    """
    Parse options のテスト
    """

    def test_parse_option_set_dic(self, client):
        """
        Test 'set-dic' option.

        Notes
        -----
        'set-dic' に r'geoshape' を指定すると、
        identifier に 'geoshape' を含む辞書だけが利用されます。

        'geoshape-city' が利用できるため、
        「和歌山市（市）」に解決されます。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': '和歌山市は晴れ。',
                'options': {'set-dic': r'geoshape'}
            },
            'id': 'test_parse_set_dic',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        prop = features[0]['properties']
        assert prop['surface'] == '和歌山市'
        assert prop['geoword_properties']['geolod_id'] == 'lQccqK'

    def test_parse_option_remove_dic(self, client):
        """
        Test 'remove-dic' option.

        Notes
        -----
        'remove-dic' に r'station' を指定すると、
        identifier に 'station' を含む辞書は利用されません。

        'geoshape-city' が利用できるため、
        「和歌山市（市）」に解決されます。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': '和歌山市は晴れ。',
                'options': {'remove-dic': r'station'}
            },
            'id': 'test_parse_remove_dic',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        prop = features[0]['properties']
        assert prop['surface'] == '和歌山市'
        assert prop['geoword_properties']['dictionary_identifier'] == \
            'geonlp:geoshape-city'

    def test_parse_option_add_dic(self, client):
        """
        Test 'add-dic' option.

        Notes
        -----
        'add-dic' に r'city' を指定すると、
        'remove-dic' で除外指定されていても、
        identifier に 'city' を含む辞書は利用されます。

        'geoshape-city' は除外対象ですが add-dic で
        指定されているため利用可能になり、
        「千代田区（区）」に解決されます。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': '千代田区は雨。',
                'options': {'remove-dic': r'geoshape',
                            'add-dic': r'city'}
            },
            'id': 'test_parse_remove_dic',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        prop = features[0]['properties']
        assert prop['surface'] == '千代田区'
        assert prop['geoword_properties']['dictionary_identifier'] == \
            'geonlp:geoshape-city'

    def test_parse_option_set_class(self, client):
        """
        Test 'set-class' option.

        Notes
        -----
        'set-class' に [r'.*', r'-鉄道施設/.*'] を指定すると、
        全ての固有名クラスから '鉄道施設/.*' を除いたものを持つ
        地名語を候補として利用します。

        「和歌山市（駅）」は鉄道施設なので除外され、
        「和歌山市（市）」に解決されます。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': '和歌山市は晴れ。',
                'options': {'set-class': [r'.*', r'-鉄道施設/.*']}
            },
            'id': 'test_parse_set_class',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        prop = features[0]['properties']
        assert prop['surface'] == '和歌山市'
        assert prop['geoword_properties']['dictionary_identifier'] == \
            'geonlp:geoshape-city'

    def test_parse_option_add_remove_class(self, client):
        """
        Test 'add-class' and 'remove-class' options.

        Notes
        -----
        'set-class' で一度に指定する代わりに、
        'add-class' で利用するクラスのリストを、
        'remove-class' で除外するクラスのリストを指定できます。

        'add-class' で [r'.*'] を、
        'remove-class' で [r'鉄道施設/.*'] を指定すると、
        全ての固有名クラスから '鉄道施設/.*' を除いたものを持つ
        地名語を候補として利用します。

        'remove-class' のリストではクラス名の先頭に '-' は不要です。

        「和歌山市（駅）」は鉄道施設なので除外され、
        「和歌山市（市）」に解決されます。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': '和歌山市は晴れ。',
                'options': {'add-class': [r'.*'],
                            'remove-class': [r'鉄道施設/.*']}
            },
            'id': 'test_parse_add_remove_class',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        prop = features[0]['properties']
        assert prop['surface'] == '和歌山市'
        assert prop['geoword_properties']['dictionary_identifier'] == \
            'geonlp:geoshape-city'


@pytest.mark.skipif(gdal_not_installed,
                    reason="GDALがインストールされていません")
class TestSpatialFilters:
    """
    SpatialFilter のテスト
    """

    def test_parse_filter_geo_contains(self, client):
        """
        Test 'geo-contains' filter.

        Notes
        -----
        'geo-contains' に GeoJSON または GeoJSON を返す URL を
        指定すると、その範囲に含まれる地名語だけが候補になります。

        東京都付近の四角形を空間範囲として指定することで
        東京都の府中駅に解決されます。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': '府中に行きます。',
                'options': {
                    'geo-contains': {
                        "type": "Polygon",
                        "coordinates": [
                            [[139.43, 35.54], [139.91, 35.54],
                             [139.91, 35.83], [139.43, 35.83],
                                [139.43, 35.54]]]
                    }}
            },
            'id': 'test_parse_geo_contains',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        prop = features[0]['properties']
        assert prop['surface'] == '府中'
        assert '京王線' in prop['geoword_properties']['hypernym']

    def test_parse_filter_geo_disjoint(self, client):
        """
        Test 'geo-disjoint' filter.

        Notes
        -----
        'geo-disjoint' に GeoJSON または GeoJSON を返す URL を
        指定すると、その範囲に含まれない地名語だけが候補になります。

        東京都付近の四角形を空間範囲として指定することで
        京都市の府中駅に解決されます。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': '府中に行きます。',
                'options': {
                    'geo-disjoint': 'https://geoshape.ex.nii.ac.jp/city/geojson/20200101/13/13208A1968.geojson'
                }
            },
            'id': 'test_parse_geo_disjoint',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        prop = features[0]['properties']
        assert prop['surface'] == '府中'
        assert '天橋立鋼索鉄道' in prop['geoword_properties']['hypernym']


class TestTemporalFilters:
    """
    TemporalFilter のテスト
    """

    sentence = ('田無市と保谷市は2001年1月21日に合併して'
                '西東京市になりました。')

    def test_time_exists(self, client):
        """
        Test 'time-exists' filter.

        Notes
        -----
        'time-exists' に日時または日時のペアを指定すると、
        その時点・期間に存在した地名語だけが候補になります。

        西東京市は指定した期間内に設置されたので
        田無市と保谷市、西東京市は全て地名語になります。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': self.sentence,
                'options': {
                    'time-exists': ['2000-01-01', '2001-02-01']
                }
            },
            'id': 'test_time_exists',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        for feature in features:
            prop = feature['properties']
            if prop['surface'] in ('田無市', '保谷市', '西東京市',):
                assert prop['node_type'] == 'GEOWORD'
            else:
                assert prop['node_type'] == 'NORMAL'

    def test_time_before(self, client):
        """
        Test 'time-before' filter.

        Notes
        -----
        'time-before' に日時または日時のペアを指定すると、
        その時点・期間の開始時より前に存在した地名語だけが
        候補になります。

        西東京市は指定した期間の開始時より後に設置されたので
        田無市と保谷市が地名語、西東京市は固有名詞になります。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': self.sentence,
                'options': {
                    'time-before': ['2000-01-01', '2001-02-01']
                }
            },
            'id': 'test_time_before',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        for feature in features:
            prop = feature['properties']
            if prop['surface'] in ('田無市', '保谷市',):
                assert prop['node_type'] == 'GEOWORD'
            elif prop['surface'] in ('西東京市',):
                assert prop['node_type'] == 'NORMAL'
            else:
                assert prop['node_type'] == 'NORMAL'

    def test_time_after(self, client):
        """
        Test 'time-after' filter.

        Notes
        -----
        'time-after' に日時または日時のペアを指定すると、
        その時点・期間の終了時より後に存在した地名語だけが
        候補になります。

        田無市と保谷市は指定した期間の終了時より前に廃止されたので
        田無市と保谷市は固有名詞、西東京市は地名語になります。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': self.sentence,
                'options': {
                    'time-after': ['2000-01-01', '2001-02-01']
                }
            },
            'id': 'test_time_after',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        for feature in features:
            prop = feature['properties']
            if prop['surface'] in ('西東京市',):
                assert prop['node_type'] == 'GEOWORD'
            elif prop['surface'] in ('田無市', '保谷市',):
                assert prop['node_type'] == 'NORMAL'
            else:
                assert prop['node_type'] == 'NORMAL'

    def test_time_overlaps(self, client):
        """
        Test 'time-overlaps' filter.

        Notes
        -----
        'time-overlaps' に日時または日時のペアを指定すると、
        その時点・期間の終了時より後に存在した地名語だけが
        候補になります。

        西東京市は指定した期間内に設置されたので
        田無市と保谷市、西東京市は全て地名語になります。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': self.sentence,
                'options': {
                    'time-overlaps': ['2000-01-01', '2001-02-01']
                }
            },
            'id': 'test_time_after',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        for feature in features:
            prop = feature['properties']
            if prop['surface'] in ('田無市', '保谷市', '西東京市',):
                assert prop['node_type'] == 'GEOWORD'
            else:
                assert prop['node_type'] == 'NORMAL'

    def test_time_covers(self, client):
        """
        Test 'time-covers' filter.

        Notes
        -----
        'time-covers' に日時または日時のペアを指定すると、
        その期間の開始時より終了時まで存在し続けた地名語だけが
        候補になります。

        西東京市は指定した期間内に設置され、
        田無市と保谷市は期間内に廃止されたので、
        田無市、保谷市、西東京市は全て固有名詞になります。
        """
        query = json.dumps({
            'method': 'geonlp.parse',
            'params': {
                'sentence': self.sentence,
                'options': {
                    'time-covers': ['2000-01-01', '2001-02-01']
                }
            },
            'id': 'test_time_covers',
        })
        expected = '*'
        result = validate_jsonrpc(client, query, expected)

        # GeoJSON Feature Collection のチェック
        assert result['type'] == 'FeatureCollection'
        assert 'features' in result
        features = result['features']

        # 地名語のチェック
        for feature in features:
            prop = feature['properties']
            assert prop['node_type'] == 'NORMAL'
