# -*- coding: utf-8 -*-
#
#   dp for Tornado
#      YoungYong Park (youngyongpark@gmail.com)
#      2014.10.23
#


import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options

import logging
import logging.handlers

import time
import os
import multiprocessing
import importlib

import application

try:
    import configparser
except:
    import ConfigParser as configparser

from engine.plugin.static import Compressor
from engine.plugin.static import StaticURL
from engine.plugin.prefix import PrefixURL
from engine.plugin.pagination import Pagination
from engine.plugin import ui_methods


class RestfulApplication(tornado.web.Application):
    def __init__(self, handlers, kwargs):
        self.startup_at = int(round(time.time() * 1000))

        kwargs['ui_modules']['Static'] = StaticURL
        kwargs['ui_modules']['Prefix'] = PrefixURL
        kwargs['ui_modules']['Pagination'] = Pagination
        kwargs['ui_methods'] = ui_methods

        super(RestfulApplication, self).__init__(handlers, **kwargs)

if __name__ == '__main__':
    # INI
    config = configparser.RawConfigParser()
    config.read('%s/config.ini' % (os.path.dirname(os.path.realpath(__file__)), ))

    def get_config(c, option, section='server', default=None):
        try:
            get = c.get(section, option)

            if default is True or default is False:
                return True if get == '1' else False

            elif isinstance(default, str):
                return str(get)

            elif isinstance(default, int):
                return int(get)

            else:
                return get
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    # Setup Options
    tornado.options.define('max_worker', default=get_config(config, 'max_worker', default=64))
    tornado.options.define('num_processes', default=get_config(config, 'num_processes', default=0))
    tornado.options.define('port', default=get_config(config, 'port', default=8080))
    tornado.options.define('debug', default=get_config(config, 'debug', default=False))
    tornado.options.define('gzip', default=get_config(config, 'gzip', default=True))
    tornado.options.define('crypto_key', default=get_config(config, 'key', section='crypto', default='CRy$t0-$CR@T'))

    # Initialize Logging
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s][%(levelname)s] %(message)s')

    logging.info('---------------------------------')
    logging.info('dp for Tornado has been started..')
    logging.info('---------------------------------')

    services = []

    for service in application.services:
        s = str.split(service[1], '.')
        class_name = s.pop()
        module_path = '.'.join(s)

        handler_module = importlib.import_module(module_path)
        handler = getattr(handler_module, class_name)

        services.append((service[0], handler, dict(prefix=module_path)))

    current_dir = os.path.dirname(os.path.realpath(__file__))
    combined_dir = '%s/static/combined' % current_dir

    # Clear combined files
    Compressor.clear(combined_dir)

    settings = {
        'template_path': '%s/view' % current_dir,
        'static_path': '%s/static' % current_dir,
        'static_url_prefix': '/s/',
        'combined_static_path': combined_dir,
        'combined_static_url_prefix': '/s/combined/',
        'compressor': {
            'yuicompressor': '%s/engine/plugin/compressor/yuicompressor-2.4.8.jar' % current_dir,
            'uglifyjs': '%s/engine/plugin/compressor/uglifyjs2/bin/uglifyjs' % current_dir,
        },
        'debug': tornado.options.options.debug,
        'gzip': tornado.options.options.gzip,
        'cookie_secret': get_config(config, 'cookie_secret', default='default_cookie_secret'),
        'ui_modules': {}
    }

    num_processed = (tornado.options.options.num_processes
                     if tornado.options.options.num_processes else multiprocessing.cpu_count())

    logging.info('Server Mode : %s' % ('Production' if not tornado.options.options.debug else 'Debugging'))
    logging.info('Server time : %s' % time.strftime('%Y.%m.%d %H:%M:%S'))
    logging.info('Server Port : %s' % tornado.options.options.port)
    logging.info('Max Workers : %s' % tornado.options.options.max_worker)
    logging.info('Processors  : %s' % num_processed)
    logging.info('CPU Count   : %d' % multiprocessing.cpu_count())
    logging.info('---------------------------------')

    application = RestfulApplication(services, settings)
    service = tornado.httpserver.HTTPServer(application, xheaders=True)
    service.bind(tornado.options.options.port, '')
    service.start(tornado.options.options.num_processes)

    import random
    application.identifier = random.randint(100000, 999999)

    try:
        instance = tornado.ioloop.IOLoop.instance()
        instance.__setattr__('startup_at', getattr(application, 'startup_at'))
        instance.start()
    except KeyboardInterrupt:
        pass
