FROM osgeo/gdal:ubuntu-full-3.6.3
# このイメージは "Ubuntu 22.04.2 LTS" を拡張しています。

ENV JAGEOCODER_DB2_DIR /opt/db2

# pygeonlp に必要なライブラリ・パッケージをインストールします。
RUN apt-get update && apt-get install -y \
    libmecab-dev \
    mecab-ipadic-utf8 \
    libboost-all-dev \
    libsqlite3-dev \
    curl \
    python3 \
    python3-dev \
    python3-pip

# pygeonlp と基本辞書セットをインストールします。
RUN python3 -m pip install pygeonlp && pygeonlp setup

# pygeonlp-webapi をインストールします。
RUN pip install pygeonlp-webapi

ENV GEONLP_MECAB_DIC_DIR=/var/lib/mecab/dic/ipadic-utf8
ENV FLASK_APP=pygeonlp_webapi.app

# 住所ジオコーダをインストールしたイメージを作りたい場合は以下のコメントを外してください。
# RUN curl https://www.info-proto.com/static/jageocoder/latest/gaiku_all_v21.zip \
#     -o /opt/gaiku_all_v21.zip && \
#     jageocoder install-dictionary /opt/gaiku_all_v21.zip && \
#     rm /opt/gaiku_all_v21.zip

# NEologd を辞書として利用したい場合は以下のコメントを外してください。
# ENV GEONLP_MECAB_DIC_DIR=/neologd
# RUN apt-get install -y git mecab
# RUN cd /tmp \
#     && git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git \
#     && cd mecab-ipadic-neologd \
#     && ./bin/install-mecab-ipadic-neologd --prefix /neologd -n -a -u -y \
#     && cd / \
#     && rm -r /tmp/mecab-ipadic-neologd

# WebAPI サーバを起動します。
CMD ["/bin/bash", "-c", "python -m flask run -h 0.0.0.0 -p 5000"]

