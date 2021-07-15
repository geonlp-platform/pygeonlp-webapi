from collections.abc import Iterable
import datetime
from typing import Any, Dict, List, Union, NoReturn, Optional
from logging.config import dictConfig
from numbers import Real
import os

from flask import Flask
from flask_jsonrpc import JSONRPC
from flask_jsonrpc.exceptions import MethodNotFoundError
from sqlite3 import OperationalError

import pygeonlp.api as geonlp_api
from pygeonlp_webapi.config.default import config

dictConfig(config.LOGGING)
app = Flask('pygeonlp_webapi')
app.config.from_object(config)
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=False)

try:
    import jageocoder
    dsn = 'sqlite:///{}'.format(os.path.join(
        config.JAGEOCODER_DIR, 'address.db'))
    jageocoder.init(dsn=dsn, trie_path=os.path.join(
        config.JAGEOCODER_DIR, 'address.trie'))
except OperationalError:
    app.logger.warning('jageocoder 辞書がディレクトリ {} に見つかりません'.format(
        config.JAGEOCODER_DIR))
    jageocoder = None
except ModuleNotFoundError:
    app.logger.info('jageocoder がインストールされていません')
    jageocoder = None


geonlp_api.init(db_dir=config.GEONLP_DIR,
                **(config.GEONLP_API_OPTIONS))


def apply_geonlp_api_parse_options(options: Optional[dict] = None):
    """
    Parse, ParseStructured のオプションに含まれる解析条件を
    geonlp_api に適用します。

    Parameters
    ----------
    options: dict, optional
        Parse オプション

    Notes
    -----
    利用可能なオプションは以下の通りで、この順番に処理されます。

    geocoding: bool
        住所ジオコーディングを利用する場合は true を指定します。

    **辞書の指定**

    set-dic: str or list
        利用する地名解析辞書の identifier のリスト、または正規表現。

    remove-dic: str or list
        除外する地名解析辞書の identifier のリスト、または正規表現。

    add-dic: str or list
        追加する地名解析辞書の identifier のリスト、または正規表現。

    **固有名クラスの指定**

    set-class: list
        解析対象とする固有名クラスの正規表現のリスト。

    add-class: list
        解析対象に追加する固有名クラスの正規表現のリスト。

    remove-class: list
        解析対象から除外する固有名クラスの正規表現のリスト。

    **フィルタの指定**

    geo-contains: str or dict
        GeoContainsFilter の範囲を表す GeoJSON または
        GeoJSON を返す URL。

    geo-disjoint: str or dict
        GeoDisjointFilter を範囲を表す GeoJSON または
        GeoJSON を返す URL。

    time-exists: str, or list of str
        TimeExistsFilter の基準日時を表す文字列、
        または期間の開始日時と終了日時を表す2つの文字列。

    time-before: str, or list of str
        TimeBeforeFilter の基準日時を表す文字列。
        期間が与えられた場合は開始日時を基準日時とします。

    time-after: str, or list of str
        TimeAfterFilter の基準日時を表す文字列。
        期間が与えられた場合は終了日時を基準日時とします。

    time-overlaps: str, or list of str
        TimeOverlapsFilter の基準日時を表す文字列、
        または期間の開始日時と終了日時を表す2つの文字列。

    time-covers: str, or list of str
        TimeCoversFilter の基準日時を表す文字列、
        または期間の開始日時と終了日時を表す2つの文字列。
    """
    if options is None:
        options = {}

    geonlp_api.setActiveDictionaries(pattern=r'.*')  # デフォルトに戻す

    if 'set-dic' in options:
        param = options.get('set-dic')
        if isinstance(param, str):
            geonlp_api.setActiveDictionaries(pattern=param)
        elif isinstance(param, Iterable):
            geonlp_api.setActiveDictionaries(idlist=param)
        else:
            raise TypeError((
                "'set-dic' には利用する辞書の id か identifier のリスト、"
                "または identifer の正規表現文字列を指定してください。"))

    if 'remove-dic' in options:
        param = options.get('remove-dic')
        if isinstance(param, str):
            geonlp_api.disactivateDictionaries(pattern=param)
        elif isinstance(param, Iterable):
            geonlp_api.disactivateDictionaries(idlist=param)
        else:
            raise TypeError((
                "'remove-dic' には除外する辞書の id か identifier のリスト、"
                "または identifer の正規表現文字列を指定してください。"))

    if 'add-dic' in options:
        param = options.get('add-dic')
        if isinstance(param, str):
            geonlp_api.activateDictionaries(pattern=param)
        elif isinstance(param, Iterable):
            geonlp_api.activateDictionaries(idlist=param)
        else:
            raise TypeError((
                "'add-dic' には追加する辞書の id か identifier のリスト、"
                "または identifer の正規表現文字列を指定してください。"))

    active_classes = []
    if 'set-class' in options:
        param = options.get('set-class')
        if isinstance(param, Iterable):
            active_classes = [str(x) for x in list(param)]
        else:
            raise TypeError((
                "'set-class' には解析対象とする固有名クラスを"
                "正規表現のリストで指定してください。"))

    if 'add-class' in options:
        param = options.get('add-class')
        if isinstance(param, Iterable):
            active_classes += [str(x) for x in list(param)]
        else:
            raise TypeError((
                "'add-class' には解析対象に追加する固有名クラスを"
                "正規表現のリストで指定してください。"))

    if 'remove-class' in options:
        param = options.get('remove-class')
        if isinstance(param, Iterable):
            active_classes += ['-' + str(x) for x in list(param)]
        else:
            raise TypeError((
                "'remove-class' には解析対象から除外する固有名クラスを"
                "正規表現のリストで指定してください。"))

    # 利用するクラス、除外するクラスの順に並べ替え
    include_classes = []
    exclude_classes = []
    for classname in active_classes:
        if classname.startswith('-'):
            exclude_classes.append(classname)
        else:
            include_classes.append(classname)

    geonlp_api.setActiveClasses(include_classes + exclude_classes)


def get_filters_from_options(options: Optional[dict] = {}):
    """
    Parse, ParseStructured のオプションに含まれる
    フィルタのリストを解析し、フィルタオブジェクトを作成して返す。
    """
    filters = []

    if 'geo-contains' in options:
        param = options.get('geo-contains')
        if isinstance(param, str):
            geojson = param
        elif isinstance(param, dict) and 'geometry' in param:
            geojson = param['geometry']
        else:
            geojson = param

        from pygeonlp.api.spatial_filter import GeoContainsFilter
        filters.append(GeoContainsFilter(geojson))

    if 'geo-disjoint' in options:
        param = options.get('geo-disjoint')
        if isinstance(param, str):
            geojson = param
        elif isinstance(param, dict) and 'geometry' in param:
            geojson = param['geometry']
        else:
            geojson = param

        from pygeonlp.api.spatial_filter import GeoDisjointFilter
        filters.append(GeoDisjointFilter(geojson))

    if 'time-exists' in options:
        param = options.get('time-exists')
        from pygeonlp.api.temporal_filter import TimeExistsFilter
        if isinstance(param, (str, datetime.date, datetime.datetime)):
            filters.append(TimeExistsFilter(param))
        elif isinstance(param, (list, tuple)):
            filters.append(TimeExistsFilter(*param))
        elif isinstance(param, dict):
            filters.append(TimeExistsFilter(**param))
        else:
            raise TypeError(
                "'time-exists' のパラメータが解析できません")

    if 'time-before' in options:
        param = options.get('time-before')
        from pygeonlp.api.temporal_filter import TimeBeforeFilter
        if isinstance(param, (str, datetime.date, datetime.datetime)):
            filters.append(TimeBeforeFilter(param))
        elif isinstance(param, (list, tuple)):
            filters.append(TimeBeforeFilter(*param))
        elif isinstance(param, dict):
            filters.append(TimeBeforeFilter(**param))
        else:
            raise TypeError(
                "'time-before' のパラメータが解析できません")

    if 'time-after' in options:
        param = options.get('time-after')
        from pygeonlp.api.temporal_filter import TimeAfterFilter
        if isinstance(param, (str, datetime.date, datetime.datetime)):
            filters.append(TimeAfterFilter(param))
        elif isinstance(param, (list, tuple)):
            filters.append(TimeAfterFilter(*param))
        elif isinstance(param, dict):
            filters.append(TimeAfterFilter(**param))
        else:
            raise TypeError(
                "'time-after' のパラメータが解析できません")

    if 'time-overlaps' in options:
        param = options.get('time-overlaps')
        from pygeonlp.api.temporal_filter import TimeOverlapsFilter
        if isinstance(param, (str, datetime.date, datetime.datetime)):
            filters.append(TimeOverlapsFilter(param))
        elif isinstance(param, (list, tuple)):
            filters.append(TimeOverlapsFilter(*param))
        elif isinstance(param, dict):
            filters.append(TimeOverlapsFilter(**param))
        else:
            raise TypeError(
                "'time-overlaps' のパラメータが解析できません")

    if 'time-covers' in options:
        param = options.get('time-covers')
        from pygeonlp.api.temporal_filter import TimeCoversFilter
        if isinstance(param, (str, datetime.date, datetime.datetime)):
            filters.append(TimeCoversFilter(param))
        elif isinstance(param, (list, tuple)):
            filters.append(TimeCoversFilter(*param))
        elif isinstance(param, dict):
            filters.append(TimeCoversFilter(**param))
        else:
            raise TypeError(
                "'time-covers' のパラメータが解析できません")

    return filters


@jsonrpc.method('geonlp.parse')
def parse(sentence: str, options: Optional[dict] = {}) -> dict:
    apply_geonlp_api_parse_options(options)
    filters = get_filters_from_options(options)
    if options.get('geocoding'):
        geocoder = jageocoder
    else:
        geocoder = None

    result = geonlp_api.geoparse(
        sentence, jageocoder=geocoder, filters=filters)

    feature_collection = {
        "type": "FeatureCollection",
        "features": result
    }

    return feature_collection


@jsonrpc.method('geonlp.parseStructured')
def parse_structured(
        sentence_list: List[str],
        options: Optional[dict] = {}) -> dict:

    apply_geonlp_api_parse_options(options)
    filters = get_filters_from_options(options)
    if options.get('geocoding'):
        geocoder = jageocoder
    else:
        geocoder = None

    result = []
    for sentence in sentence_list:
        result += geonlp_api.geoparse(
            sentence, jageocoder=geocoder, filters=filters)

    feature_collection = {
        "type": "FeatureCollection",
        "features": result
    }

    return feature_collection


@jsonrpc.method('geonlp.search')
def search(key: str, options: Optional[dict] = None) -> dict:
    """
    Method ``geonlp.search``
    任意の地名語の情報をデータベースから検索します。

    Parameters
    ----------
    key: str
        検索する語
    options: dict
        Parse オプション

    Returns
    -------
    dict
        geolod_id をキー、地名語の情報を値に持つ dict
    """
    apply_geonlp_api_parse_options(options)
    return geonlp_api.searchWord(key)


@jsonrpc.method('geonlp.getGeoInfo')
def get_geo_info(idlist: List[str], options: Optional[dict] = None) -> dict:
    """
    Method ``geonlp.getGeoInfo``
    指定した geolod_id を持つ語の情報を返します。
    id が辞書に存在しない場合は None を返します。

    Parameters
    ----------
    idlist: str or list
        検索する語の geolod_id または geolod_id のリスト
    options: dict
        Parse オプション

    Returns
    -------
    dict
        geolod_id をキー、地名語の情報を値に持つ dict
    """
    apply_geonlp_api_parse_options(options)
    return geonlp_api.getWordInfo(idlist)


@jsonrpc.method('geonlp.getDictionaries')
def get_dictionaries(options: Optional[dict] = None) -> list:
    """
    Method ``geonlp.getDictionaries``
    データベースに登録されている地名解析辞書の
    identifier のリストを返します。

    Parameters
    ----------
    options: dict
        Parse オプション

    Returns
    -------
    list
        identifier のリスト
    """
    apply_geonlp_api_parse_options(options)
    return sorted(
        [x.get_identifier() for x in geonlp_api.getDictionaries()]
    )


@jsonrpc.method('geonlp.getDictionaryInfo')
def get_dictionary_info(
        identifier: str,
        options: Optional[dict] = None) -> Union[str, None]:
    """
    Method ``geonlp.getDictionaryInfo``
    指定された identifer を持つ地名解析辞書の JSONLD
    メタデータをデータベースから取得します。

    Parameters
    ----------
    identifier: str
        地名解析辞書の identifier
    options: dict
        Parse オプション

    Returns
    -------
    str
        jsonld メタデータ文字列

        identifier と一致する辞書が存在しない場合は None
    """
    apply_geonlp_api_parse_options(options)
    metadata = geonlp_api.getDictionary(identifier)
    if metadata:
        return metadata.jsonld

    return None


@jsonrpc.method('geonlp.addressGeocoding')
def address_geocoding(address: str) -> dict:
    """
    Method ``geonlp.addressGeocoding``
    住所ジオコーディングした結果を返します。

    Parameters
    ----------
    address: str
        住所文字列

    Returns
    -------
    dict
        住所ジオコーディングの結果
    """
    if jageocoder is None:
        raise MethodNotFoundError(
            message="'addressGeocoding' is not available on this server.")

    return jageocoder.search(address)


if __name__ == '__main__':
    app.run(debug=config.DEBUG)
