# -*- coding: utf-8 -*-
#
#   dp for Tornado
#      YoungYong Park (youngyongpark@gmail.com)
#      2014.10.23
#


from .engine import Engine as dpEngine
from .singleton import Singleton as dpSingleton
from .loader import Loader as dpLoader

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

import threading


class InValueModelConfig(object):
    def __init__(self, driver=None, database=None, host=None, user=None, password=None, port=None, path=None, pure=None):
        self.driver = driver
        self.database = database
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.path = path
        self.pure = pure

    def __getattr__(self, name):
        try:
            attr = self.__getattribute__(name)
        except AttributeError:
            attr = None

        return attr

    def __str__(self):
        return 'InValueModelConfig (%s://%s:%s@%s:%s/%s/%s) (Pure:%s)' \
               % (self.driver, self.user, self.password, self.host, self.port, self.database, self.path, self.pure)


class ModelSingleton(dpEngine, dpSingleton):
    _lock = threading.Lock()

    @property
    def engines(self):
        if not hasattr(self, '_engines'):
            self._engines = {}

        return self._engines

    def _parse_config(self, config_dsn, delegate, cache=False):
        if isinstance(config_dsn, InValueModelConfig):
            delegate['config'] = 'InValueModelConfig'
            delegate['database'] = config_dsn.database
            delegate['key'] = '%s_%s' % (config_dsn.driver, config_dsn.database)

            return config_dsn

        config_dsn = config_dsn.split('/')

        config = config_dsn[0]
        database = config_dsn[1]

        delegate['config'] = config
        delegate['database'] = database
        delegate['key'] = '%s_%s' % (delegate['config'], delegate['database'])

        if delegate['key'] in ModelSingleton().engines:
            return True

        try:
            package = config.split('.')
            conf = self.config

            for p in package:
                conf = conf.__getattr__(p)

            if not cache:
                conf = conf.databases.__getattr__(database)

            else:
                conf = conf.caches.__getattr__(database)

        except AttributeError:
            conf = None

        return conf

    def engine(self, config_dsn, cache=False):
        delegate = {}
        conf = self._parse_config(config_dsn, delegate, cache=cache)

        if not conf:
            return None

        if not delegate['key'] in ModelSingleton().engines:
            ModelSingleton._lock.acquire()

            if conf.driver == 'memory':
                import os
                abspath = os.path.dirname(os.path.realpath(__file__))
                path = '%s/../resource/database/sqlite/cache_%s_%s.db' \
                       % (abspath, delegate['config'], delegate['database'])

                connection_args = {'check_same_thread': False}
                connection_url = 'sqlite:///%s' % path

            elif conf.driver == 'sqlite':
                if conf.path:
                    path = conf.path
                else:
                    import os
                    abspath = os.path.dirname(os.path.realpath(__file__))
                    path = '%s/../resource/database/sqlite/%s_%s.db' \
                           % (abspath, delegate['config'], delegate['database'])

                connection_args = {'check_same_thread': False}
                connection_url = 'sqlite:///%s' % path

            else:
                connection_args = {}
                connection_url = '%s://%s:%s@%s:%s/%s' % (
                    conf.driver,
                    conf.user, conf.password,
                    conf.host, conf.port,
                    conf.database)

            params = {
                'convert_unicode':conf.convert_unicode if conf.convert_unicode is not None else True,
                'echo':conf.echo if conf.echo is not None else False,
                'echo_pool':conf.echo_pool if conf.echo_pool is not None else False,
                'pool_size':conf.pool_size if conf.pool_size is not None else 16,
                'poolclass':QueuePool,
                'pool_recycle':conf.pool_recycle if conf.pool_recycle is not None else 3600,
                'max_overflow':conf.max_overflow if conf.max_overflow is not None else -1,
                'pool_timeout':conf.pool_timeout if conf.pool_timeout is not None else 30,
                'connect_args':connection_args
            }

            if conf.isolation_level is not None:
                params['isolation_level'] = conf.isolation_level

            ModelSingleton().engines[delegate['key']] = create_engine(connection_url, **params)

            ModelSingleton._lock.release()

        return ModelSingleton().engines[delegate['key']]

    def getconn(self, config_dsn, cache=False):
        engine = ModelSingleton().engine(config_dsn, cache=cache)

        if not engine:
            return None

        return engine.connect()

    def begin(self, dsn_or_conn, cache=False):
        config_dsn = dsn_or_conn if isinstance(dsn_or_conn, (str, InValueModelConfig)) else None
        connection = self.getconn(config_dsn, cache=cache) if config_dsn else dsn_or_conn
        transaction = connection.begin()

        return ModelProxy(connection, transaction)

    def commit(self, proxy, return_connection=True):
        result = proxy.transaction.commit()

        if return_connection:
            proxy.connection.close()

        return result

    def rollback(self, proxy, return_connection=True):
        result = proxy.transaction.rollback()

        if return_connection:
            proxy.connection.close()

        return result

    def close(self, proxy):
        return proxy.connection.close()

    def execute(self, sql, bind=None, dsn_or_conn=None, cache=False):
        config_dsn = dsn_or_conn if isinstance(dsn_or_conn, (str, InValueModelConfig)) else None
        conn = self.getconn(config_dsn, cache=cache) if config_dsn else dsn_or_conn
        conn = conn.connection if isinstance(conn, ModelProxy) else conn

        if isinstance(bind, dict):
            result = conn.execute(sql, **bind)
        elif isinstance(bind, list):
            result = conn.execute(sql, *bind)
        elif bind is not None:
            result = conn.execute(sql, (bind, ))
        else:
            result = conn.execute(sql)

        if config_dsn:
            conn.close()

        return result

    def row(self, sql, bind=None, dsn_or_conn=None, cache=False):
        config_dsn = dsn_or_conn if isinstance(dsn_or_conn, (str, InValueModelConfig)) else None
        conn = self.getconn(config_dsn, cache=cache) if config_dsn else dsn_or_conn
        result = self.execute(sql, bind, dsn_or_conn=conn, cache=cache)
        row = None

        for r in result:
            row = r
            break

        if config_dsn:
            conn.close()

        return row

    def rows(self, sql, bind=None, dsn_or_conn=None, cache=False):
        config_dsn = dsn_or_conn if isinstance(dsn_or_conn, (str, InValueModelConfig)) else None
        conn = self.getconn(config_dsn, cache=cache) if config_dsn else dsn_or_conn
        result = self.execute(sql, bind, dsn_or_conn=conn, cache=cache)

        rows = []

        for r in result:
            rows.append(r)

        if config_dsn:
            conn.close()

        return rows


class ModelProxy(object):
    def __init__(self, connection, transaction):
        self._connection = connection
        self._transaction = transaction

    @property
    def connection(self):
        return self._connection

    @property
    def transaction(self):
        return self._transaction

    def commit(self, return_connection=True):
        return ModelSingleton().commit(self, return_connection)

    def rollback(self, return_connection=True):
        return ModelSingleton().rollback(self, return_connection)

    def close(self):
        return ModelSingleton().close(self)

    def execute(self, sql, bind=None, dsn_or_conn=None):
        return ModelSingleton().execute(sql, bind, dsn_or_conn or self)

    def row(self, sql, bind=None, dsn_or_conn=None):
        return ModelSingleton().row(sql, bind, dsn_or_conn or self)

    def rows(self, sql, bind=None, dsn_or_conn=None):
        return ModelSingleton().rows(sql, bind, dsn_or_conn or self)


class Model(dpEngine, dpLoader):
    def _getconn(self, config_dsn):
        return ModelSingleton().getconn(config_dsn)

    def begin(self, dsn_or_conn):
        return ModelSingleton().begin(dsn_or_conn)

    def commit(self, proxy, return_connection=True):
        return ModelSingleton().commit(proxy, return_connection)

    def rollback(self, proxy, return_connection=True):
        return ModelSingleton().rollback(proxy, return_connection)

    def close(self, proxy):
        return ModelSingleton().close(proxy)

    def execute(self, sql, bind=None, dsn_or_conn=None):
        return ModelSingleton().execute(sql, bind, dsn_or_conn)

    def row(self, sql, bind=None, dsn_or_conn=None):
        return ModelSingleton().row(sql, bind, dsn_or_conn)

    def rows(self, sql, bind=None, dsn_or_conn=None):
        return ModelSingleton().rows(sql, bind, dsn_or_conn)