# -*- coding: utf-8 -*-


from dp_tornado.engine.controller import Controller as dpController


class UrlsController(dpController):
    @dpController.route('^test/(\d)/(.*)/(.*)$')  # -> test/1/a/b -> 404
    @dpController.route('^test-1$')  # -> test-1 -> done!
    @dpController.route('^test-2$')  # -> test-2 -> done!
    def get(self):
        self.finish('done!')
