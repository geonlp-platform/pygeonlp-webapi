FROM Python:3.8.13

ARG project_dir=/api
RUN mkdir -p $project_dir
WORKDIR $project_dir

RUN apt-get update && apt-get install -y wget
RUN apt-get install -y libboost-all-dev
RUN apt-get install -y libmecab-dev mecab-ipadic-utf8
RUN apt-get install -y libgdal-dev
RUN pip install --upgrade pip setuptools
RUN pip install pygeonlp-webapi

COPY Docker/runscript.py $project_dir/runscript.py
RUN python $project_dir/runscript.py
ENV MECAB_DIC_DIR=/var/lib/mecab/dic/ipadic-utf8
ENV FLASK_APP=$project_dir/pygeonlp_webapi/app.py
CMD ["flask", "run", "-h", "0.0.0.0"]

