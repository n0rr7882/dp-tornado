# -*- coding: utf-8 -*-


from dp_tornado.engine.helper import Helper as dpHelper


class UrlHelper(dpHelper):
    def validate(self, e):
        return self.helper.validator.url.validate(e)
