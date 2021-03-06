# -*- coding: utf-8 -*-

import os
import shutil
import logging

from tornado.web import stream_request_body
from tornado.httputil import parse_body_arguments
from tornado import gen

from service import PackageService as pkg_service

from controller.common import BaseHandler

from setting.config import system


logger = logging.getLogger('PackageController')


class UploadHandler(BaseHandler):
    def get(self):
        self.render('package/upload.html')


@stream_request_body
class UploadMultipartHandler(BaseHandler):
    @gen.coroutine
    def data_received(self, chunk):
        content_type = self.request.headers["Content-Type"]
        arguments, files = {}, {}
        parse_body_arguments(content_type, chunk, arguments, files)

        content_type = self.request.headers["Content-Type"]
        arguments, files = {}, {}
        parse_body_arguments(content_type, chunk, arguments, files)

        # total = int(arguments.get('chunks', ['0'])[0])
        index = int(arguments.get('chunk', ['0'])[0])

        uuid = arguments['uuid'][0]
        file_id = arguments['id'][0]
        # name = arguments['name'][0]

        directory = os.path.join(system['temporary_path'], uuid, file_id)
        if not os.path.exists(directory): os.makedirs(directory)

        with open(os.path.join(directory, str(index)), 'wb+') as fout:
            fout.write(files['file'][0].get('body', ''))
        
        logger.info('recieved and saved chunk {0}'.format(index))

    def post(self):
        self.well_done()


class UploadNotifyHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        uuid = self.get_argument('uuid')
        file_id = self.get_argument('fileId')
        fname = self.get_argument('filename')
        agent_id = self.get_argument('agent_id')

        directory = os.path.join(system['temporary_path'], uuid, file_id)
        total = sum(os.path.isfile(os.path.join(directory, x)) for x in os.listdir(directory))

        output_filename = os.path.join(system['packages_path'], fname)
        with open(output_filename, 'wb+') as fout:
            for index in range(total):
                chunk = os.path.join(directory, str(index))
                stream = open(chunk, 'rb').read()
                fout.write(stream)
        
        logger.info('file merged: {0}'.format(fname))
        
        # shutil.rmtree(directory)

        # count = sum(os.path.isfile(os.path.join(directory, '..')) for x in os.walk(directory))
        # if count == 0:
        #     shutil.rmtree(os.path.join(system['temporary_path'], uuid))

        pkg_service.save(agent_id, fname)

        self.well_done()

