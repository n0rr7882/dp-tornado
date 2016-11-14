# -*- coding: utf-8 -*-


import time
import requests
import logging

try:
    from . import consts
except (ValueError, SystemError):
    import consts


def req(session, method, url, params=None, retry=3, retry_delay=1, host=None):
    session = session if session else requests.Session()
    url = '%s%s' % (consts.dp_testing_path if not host else host, url)

    for e in range(retry):
        try:
            if method == 'get':
                o = session.get(url, data=params)
            elif method == 'post':
                o = session.post(url, data=params)
            elif method == 'put':
                o = session.put(url, data=params)
            elif method == 'delete':
                o = session.delete(url, data=params)
            elif method == 'head':
                o = session.head(url, data=params)
            else:
                raise Exception('Invalid method.')

            return session, o

        except Exception as e:
            logging.exception(e)

            time.sleep(retry_delay)

    logging.error(url)
    logging.error(method)

    assert False


def req_text(method, url, params=None, retry=3, retry_delay=1, session=None, host=None):
    session, o = req(
        session=session, url=url, method=method, params=params, retry=retry, retry_delay=retry_delay, host=host)

    return session, o.status_code, o.text


def expecting_text(
        method, url, expected, expect_code=200, params=None, retry=3, retry_delay=1, session=None, host=None):
    session, status_code, response = req_text(
        url=url, method=method, params=params, retry=retry, retry_delay=retry_delay, session=session, host=host)

    if status_code == expect_code and (expected is None or response == expected):
        return session

    logging.error('URL : [%s] %s' % (method.upper(), url))
    logging.error('Expected : %s, %s' % (expect_code, expected))
    logging.error('Resulting : %s, %s' % (status_code, response))

    assert False
