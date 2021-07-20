import glob
import json
import os
import urllib.parse
import sys

import pytest

import pygeonlp.api as geonlp_api
from pygeonlp_webapi.app import app
from pygeonlp_webapi.config.default import config


@pytest.fixture(scope="session", autouse=True)
def createTempDatabase(tmp_path_factory):
    """
    テスト用に一時的な GeoNLP データベースを作成します。
    テストを実行する際に一度だけ実行されます。
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
    """
    各テスト実行前に自動的に行なう処理を呼びだします。
    """
    app.config['TESTING'] = True


@pytest.fixture
def client():
    """
    Flask アプリケーションのテストクライアントを返します。
    """
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope="session")
def require_gdal():
    try:
        import gdal
    except ModuleNotFoundError:
        pytest.skip("Skip (GDAL not installed)")
