.. _install_pygeonlp_webapi:

インストール手順
================

pygeonlp-webapi は `pygeonlp <https://github.com/geonlp-platform/pygeonlp>`_ と
`flask-jsonrpc <https://github.com/cenobites/flask-jsonrpc>`_
を利用します。
python 3.6.8 以降で利用できます。

インストールするには pip コマンドを利用します。 ::

  pip install pygeonlp-webapi

pygeonlp がインストールされていない場合、
自動的に pygeonlp のインストールも行なわれますが、
libboost を事前に適切に設定しておかないと
コンパイルの途中で失敗することがあります。

その場合は `pygeonlp のインストール手順 <https://geonlp.ex.nii.ac.jp/doc/pygeonlp/install.html>`_
を参照し、先に pygeonlp をインストールしてから 
pygeonlp-webapi をインストールしてください。


.. _setup_pygeonlp_webapi:

インストール後の作業
--------------------

**データベースの作成**

pygeonlp-webapi には検索対象となる地名語のデータベースを作成する機能は
ありませんので、 pygeonlp でデータベースを作成してください。
データベースの作成方法は
`インストール後の設定作業 <https://geonlp.ex.nii.ac.jp/doc/pygeonlp/install.html#setup-pygeonlp>`_
を参照してください。

**サーバ設定**

以下の設定値を変更することができます。

- 地名語データベースのディレクトリ

  pygeonlp が利用するデータベースのディレクトリを指定します。

  - 環境変数 ``GEONLP_DB_DIR`` を設定すると、そのディレクトリにある
    地名語データベースを利用します

  - ``GEONLP_DB_DIR`` が設定されておらず、 ``HOME`` が設定されていると、
    ``$HOME/geonlp/db/`` にある地名語データベースを利用します

  - 環境変数を利用せずに直接設定したい場合は
    ``pygeonlp_webapi/config/default.py`` の
    ``GEONLP_DIR =`` にディレクトリのパスを書いてください

- 住所ジオコーダの辞書ディレクトリ

  jageocoder が利用する住所辞書のディレクトリを指定します。

  - 環境変数 ``JAGEOCODER_DB_DIR`` を設定すると、そのディレクトリにある
    住所辞書を利用します

  - ``JAGEOCODER_DB_DIR`` が設定されていない場合、 jageocoder の
    デフォルト値である ``{sys.prefix}/jageocoder/db/`` または
    ``{site.USER_DATA}/jageocoder/db/`` から住所辞書を探します

  - 環境変数を利用せずに直接設定したい場合は
    ``pygeonlp_webapi/config/default.py`` の
    ``JAGEOCODER_DIR =`` にディレクトリのパスを書いてください

- MeCab システム辞書ディレクトリ

  形態素解析器 MeCab が利用する辞書ディレクトリを指定します。
  デフォルト値はインストールした方法によって異なりますが、
  コマンドラインで ``mecab-config --dicdir`` を実行して確認できます。

  - 環境変数 ``MECAB_DIC_DIR`` を設定すると、そのディレクトリにある
    システム辞書を利用します（NEologd を使いたい場合など）

  - 環境変数を利用せずに直接設定したい場合は
    ``pygeonlp_webapi/config/default.py`` の
    ``MECAB_DIC_DIR =`` にディレクトリのパスを書いてください


サーバの起動
------------

テストサーバを起動するには次のコマンドを実行します。 ::

  $ FLASK_APP="pygeonlp_webapi.app" flask run --port=5000

他のマシンからアクセスする必要がある場合は ``--host=0.0.0.0``
も指定してください。 ``Ctrl+C`` で終了します。

テストサーバは Flask を利用しますので、テスト目的以外では
他の WSGI サーバを利用する必要があります。

たとえば Gunicorn を利用する場合は次のように実行してください。 ::

  $ pip install gunicorn
  $ gunicorn pygeonlp_webapi.app:app --bind=127.0.0.1:5000

``--bind`` はこのサーバにアクセスできるホストとポートを指定します。
どこからでもアクセスできるサービスをポート 8000 で公開したい場合は
``--bind=0.0.0.0:8000`` のように指定してください。

**データベースのパスを指定する場合**

デフォルト以外のディレクトリにデータベースを作成した場合は
サーバを起動する前に環境変数 ``GEONLP_DB_DIR`` に
データベースを作成したディレクトリのパスをセットしてください。 ::

  $ export GEONLP_DB_DIR=/usr/local/share/geonlp/db/

**NEologを利用する場合**

MeCab システム辞書として
`NEolog <https://github.com/neologd/mecab-ipadic-neologd/>`_
などデフォルトの IPADIC 以外の辞書を利用する場合、
サーバを起動する前に環境変数 ``MECAB_DIC_DIR`` に
辞書ディレクトリのパスをセットしてください。 ::

  $ export MECAB_DIC_DIR=$HOME/mecab-ipadic-neologd/


ブラウザ上でのテスト
--------------------

``flask-jsonrpc`` の web browsable API 機能を利用して、
ブラウザ上で API の確認とテストを行なうことができます。

サービス起動後、``Web brosable API`` の URL (
デフォルトでは ``http://127.0.0.1:5000/api/browse/`` )
を開き、動作確認したいメソッドを左メニューから選択します。


pygeonlp_webapi のアンインストール
----------------------------------

pygeonlp が不要になった場合は以下のコマンドでアンインストールできます。 ::

  $ pip uninstall pygeonlp-webapi
