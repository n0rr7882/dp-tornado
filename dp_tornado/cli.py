# -*- coding: utf-8 -*-


from dp_tornado.engine.engine import Engine as dpEngine
from dp_tornado.engine.bootstrap import Bootstrap as EngineBootstrap
from dp_tornado.version import __version_info__


class CliHandler(dpEngine):
    def __init__(self):
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('action', nargs=1)
        parser.add_argument('options', nargs='*')
        parser.add_argument('--identifier', help='Identifier')
        parser.add_argument('--path', help='App Path')
        parser.add_argument('--port', type=int, help='Binding port')

        self.parser = parser
        self.args = parser.parse_args()
        self.cwd = self.helper.io.path.cwd()

    def main(self):
        self.logging.info('------------------------')
        self.logging.info('* dp for Python v%s' % '.'.join([str(e) for e in __version_info__]))
        self.logging.info('------------------------')

        for e in self.args.options:
            if not self.args.path:
                path = self.helper.io.path.join(self.cwd, e)
                
                if self.helper.io.path.is_file(path) or \
                        (self.helper.io.path.mkdir(path) and self.helper.io.path.is_dir(path)):
                    self.args.path = e

        if self.args.action and self.args.action[0] == 'init':
            self.command_init()

        elif self.args.action and self.args.action[0] == 'run':
            self.command_run()

        else:
            self.logging.info('* dp4p finished, unrecognized action.')

    def command_init(self):
        init_dir = self.helper.io.path.join(self.cwd, self.args.path) if self.args.path else self.cwd
        installable = True

        if init_dir.endswith('__init__.py'):
            init_dir = self.helper.io.path.dirname(init_dir)

        self.logging.info('* Initializing app .. %s' % init_dir)

        if self.helper.io.path.is_dir(init_dir):
            browse = self.helper.io.path.browse(init_dir)
            browse = [e for e in browse if not self.helper.io.path.split(e)[1].startswith('.')]

            if len(browse) > 0:
                status = 'Not Empty'
                installable = False
            else:
                status = 'Empty'

        elif self.helper.io.path.is_file(init_dir):
            status = 'File'
            installable = False

        else:
            self.helper.io.path.mkdir(init_dir)

            if not self.helper.io.path.is_dir(init_dir):
                status = 'Permission Denied'
                installable = False
            else:
                status = 'Empty'

        if not installable:
            self.logging.info('* Initialization failed, %s' % status)
            return

        engine_path = self.helper.io.path.dirname(__file__)
        application_path = init_dir

        # template initialization.
        if not EngineBootstrap.init_template(engine_path=engine_path, application_path=application_path):
            self.logging.info('* Initialization failed.')
            return

        self.logging.info('* Initialization succeed.')

    def command_run(self):
        init_path = self.helper.io.path.join(self.cwd, self.args.path) if self.args.path else self.cwd
        init_path = init_path[:-1] if init_path.endswith('/') else init_path

        if init_path.endswith('__init__.py'):
            init_path = self.helper.io.path.dirname(init_path)

        init_py = init_path
        executable = True

        if self.helper.io.path.is_dir(init_py):
            init_py = '%s/__init__.py' % init_py

        self.logging.info('* Running app .. %s' % init_py)

        if not self.helper.io.path.is_file(init_py):
            executable = False

        if not executable:
            self.logging.info('* Running failed, Not executable path.')
            return

        modules = []
        dirpath = init_path

        while True:
            dirpath, module = self.helper.io.path.split(dirpath)
            modules.append(module)

            if not self.helper.io.path.is_file(self.helper.io.path.join(dirpath, '__init__.py')):
                break

        app_module = '.'.join(modules[::-1])

        self.helper.io.path.sys.insert(0, dirpath)
        self.helper.io.path.sys.insert(1, init_path)

        import sys

        __import__(app_module)
        app = sys.modules[app_module] if app_module in sys.modules else None
        app_run = getattr(app, 'run', None) if app else None

        if not app_run:
            self.logging.info('* Running failed, Invalid app.')
            return

        for i in range(len(self.args.options) + 1):
            sys.argv.pop(1)

        argv_path = sys.argv.index('--path') if '--path' in sys.argv else -1

        if argv_path >= 0:
            sys.argv.pop(argv_path)
            sys.argv.pop(argv_path)

        try:
            app_run(True)

        except KeyboardInterrupt:
            pass

        except Exception as e:
            self.logging.exception(e)


cli = CliHandler()


def main(as_module=False):
    cli.main()


if __name__ == '__main__':
    main(as_module=True)