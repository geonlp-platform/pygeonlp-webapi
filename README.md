# pygeonlp-webapi, A json-rpc webapi server for pygeonlp

This feature has been integrated into
[pygeonlp](https://github.com/geonlp-platform/pygeonlp) v.1.2.2.
It will no longer be maintained. 

`pygeonlp-webapi` is a WSGI module to use pygeonlp features as a JSON-RPC web service.

## How To Use

The server for development using Flask can be run with the following command.

```shell
$ python -m pygeonlp_webapi.app

or

$ FLASK_APP="pygeonlp_webapi.app" flask run --port=5000
```

If you prefer gunicorn, you can run the following command.

```shell
$ gunicorn pygeonlp_webapi.app:app --bind=127.0.0.1:5000
```

Then, post a JSON-RPC message to the server.

```shell
$ curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "geonlp.parse", "params":{"sentence":"NIIは千代田区にあります。"}, "id":"1"}' http://localhost:5000/api
```

More detailed Japanese documentation of the software including API is
available under <a href="doc/">`/doc`</a> directory.
You can also find the latest online documentation at
[Web Service section in GeoNLP Documentation](http://geonlp.ex.nii.ac.jp/doc/pygeonlp/webapi_doc/index.html).

## Pre-requirements

`pygeonlp-webapi` requires [pygeonlp](https://github.com/geonlp-platform/pygeonlp) and 
[flask-jsonrpc](https://github.com/cenobites/flask-jsonrpc).

## Install

The pygeonlp-webapi package can be installed with the `pip` command.
It is recommended that you upgrade pip and setuptools to
the latest versions before running it.

```sh
$ pip install --upgrade pip setuptools
$ pip install pygeonlp-webapi
```

The database needs to be prepared the first time.

**Prepare the database**

Execute the command to register the basic place name word analysis dictionaries
(`*.json`, `*.csv`) in this package into the database under the default diretory.

```
$ python -m pygeonlp.api setup
```

### Run tests (Optional)

Run the unit tests with `pytest` command.


## Uninstall

Use `pip` command to uninstall.

```sh
$ pip uninstall pygeonlp-webapi
```

## License

[The 2-Clause BSD License](https://licenses.opensource.jp/BSD-2-Clause/BSD-2-Clause.html)

## Acknowledgements

This software is supported by DIAS (Data Integration and Analysis System) and
ROIS-DS CODH (Center for Open Data in the Humanities).

It was also supported by JST (Japan Science and Technology Agency) PRESTO program.
