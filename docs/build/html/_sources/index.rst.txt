.. _pygeonlp_webapi:

ウェブサービス機能
==================

JavaScript などで構築されたウェブアプリケーションや、
Python 以外の言語で開発したアプリケーションから、
地名語辞書を検索したりテキストのジオパージング処理を行ないたい場合、
pygeonlp の解析・検索機能を利用したウェブサービスとして
提供する拡張モジュール
`pygeonlp-webapi <https://github.com/geonlp-platform/pygeonlp-webapi>`_
を利用できます。

.. toctree::
   :maxdepth: 2

   install.rst
   run_server.rst
   run_docker.rst

WebAPI の使い方
---------------

pygeonlp-webapi は `JSON-RPC 2.0 <http://json-rpc.org/>`_ 
を利用します。

サービスのエンドポイント ``/api`` に JSON 
リクエストメッセージを POST し、
JSON レスポンスを受け取ります。 ::

  $ curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0", "method": "geonlp.parse", "params": {"sentence": "NIIは神保町駅から徒歩7分です。"}, "id": "test_parse"}' http://localhost:5000/api

WebAPI およびオプションは状態を保持しません。
つまり、直前にどのようなリクエストを実行したかに関わらず、
同じリクエストを送れば同じレスポンスが返ります。

ただしサーバ側のバージョンやデータベースが変更された場合は、
結果が変わることがあります。

.. _pygeonlp_webapi_methods:

WebAPI 一覧
-----------

WebAPI メソッドの一覧です。

.. toctree::
   :maxdepth: 1

   webapi_parse.rst
   webapi_parseStructured.rst
   webapi_search.rst
   webapi_getGeoInfo.rst
   webapi_getDictionaries.rst
   webapi_getDictionaryInfo.rst
   webapi_addressGeocoding.rst


.. _pygeonlp_webapi_parse_option:

Parse オプション
----------------

WebAPI で利用する地名語の地名解析辞書や固有名クラスを
指定したり、結果に対して適用するフィルタを指定できます。

Parse オプションの一覧です。

.. toctree::
   :maxdepth: 1

   option_geocoding.rst
   option_set_dic.rst
   option_remove_dic.rst
   option_add_dic.rst
   option_set_class.rst
   option_remove_class.rst
   option_add_class.rst
   option_geo_contains.rst
   option_geo_disjoint.rst
   option_time_exists.rst
   option_time_before.rst
   option_time_after.rst
   option_time_overlaps.rst
   option_time_covers.rst
