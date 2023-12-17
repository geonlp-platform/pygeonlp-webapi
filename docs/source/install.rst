.. _install_pygeonlp_webapi:

インストール手順
================

pygeonlp-webapi は
`pygeonlp <https://github.com/geonlp-platform/pygeonlp>`_ と
`flask-jsonrpc <https://github.com/cenobites/flask-jsonrpc>`_
を利用します。
python 3.6.8 以降で利用できます。

インストールするには pip コマンドを利用します。 ::

  pip install pygeonlp-webapi

pygeonlp がインストールされていない場合、
自動的に pygeonlp のインストールも行なわれますが、
libboost を事前に適切に設定しておかないと
コンパイルの途中で失敗することがあります。

その場合は
`pygeonlp のインストール手順 <https://pygeonlp.readthedocs.io/latest/install.html>`_
に従って先に pygeonlp をインストールしてから 
pygeonlp-webapi をインストールしてください。


.. _setup_pygeonlp_webapi:

インストール後の作業
--------------------

**データベースの作成**

pygeonlp-webapi には検索対象となる地名語のデータベースを作成する機能は
ありませんので、 pygeonlp コマンドでデータベースを作成してください。 ::

  $ pygeonlp setup

で基本辞書セットがインストールされたデータベースを作成します。

データベースの管理方法については pygeonlp リファレンスの
`基本辞書セットをインストール <https://pygeonlp.readthedocs.io/latest/cli.html#cli-setup>`_
以降の説明を参照してください。


アンインストール
----------------

pygeonlp-webapi が不要になった場合は
以下のコマンドでアンインストールできます。 ::

  $ pip uninstall pygeonlp-webapi
