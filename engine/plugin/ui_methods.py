# -*- coding: utf-8 -*-
#
#   dp for Tornado
#     YoungYong Park (youngyongpark@gmail.com)
#     2014.11.21
#


import tornado.escape


def trim(c, t):
    return t.strip()

def nl2br(c, t, escape=True):
    t = tornado.escape.xhtml_escape(t) if escape else t
    return t.replace('\r\n', '<br />').replace('\r', '<br />').replace('\n', '<br />')

def yyyymmdd(c, t, s='.'):
    return c.helper.datetime.yyyymmdd(s=s, d=t)

def hhiiss(c, t, s=':'):
    return c.helper.datetime.hhiiss(s=s, d=t)