# -*- coding: utf-8 -*-


import os

from dp_tornado import Bootstrap


os.environ['TZ'] = 'Europe/London'

kwargs = {
    'application_path': os.path.join(os.path.dirname(os.path.realpath(__file__))),
    'service': [
        #(r"/post/multipart/(.*)", 'controller.post.multipart.MultipartHandler'),
    ],
    'scheduler': [
        ('22 16 * * *', 'scheduler.foo'),
        (600, 'scheduler.tests.periodic.iter_2', {'iter': 2, 'mode': 'web'}),
        (600, 'scheduler.tests.periodic.iter_1', {'iter': 1, 'mode': 'process'})
    ]
}

bootstrap = Bootstrap()
bootstrap.run(**kwargs)
