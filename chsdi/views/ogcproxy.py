# -*- coding: utf-8 -*-

import requests
from urlparse import urlparse

from pyramid.view import view_config

from pyramid.httpexceptions import HTTPBadRequest, HTTPBadGateway, HTTPNotAcceptable
from pyramid.response import Response
from chsdi.lib.decorators import requires_authorization


from StringIO import StringIO
from zipfile import ZipFile


allowed_hosts = (
    # list allowed hosts here (no port limiting)
)

DEFAULT_ENCODING = 'utf-8'


class OgcProxy:

    def __init__(self, request):
        self.request = request

    @requires_authorization()
    @view_config(route_name='ogcproxy')
    def ogcproxy(self):

        url = self.request.params.get('url')
        if url is None:
            return HTTPBadRequest('No url parameter was found')

        # Check for full url
        parsed_url = urlparse(url)
        if not parsed_url.netloc or parsed_url.scheme not in ('http', 'https'):
            raise HTTPBadRequest()

        # Forward request to target (without Host Header)
        h = dict(self.request.headers)
        h.pop('Host', h)
        try:
            resp = requests.request(
                self.request.method,
                url,
                headers=h,
                data=self.request.body
            )
        except Exception, e:
            raise HTTPBadGateway(e)

        ct = resp.headers.get('content-type')
        #  All content types are allowed
        if ct:
            if ct == 'application/vnd.google-earth.kmz':
                try:
                    with ZipFile(StringIO(resp.content)) as zipfile:
                        content = zipfile.extractall()
                    ct = 'application/vnd.google-earth.kml+xml'
                except:
                    raise HTTPBadGateway()
            else:
                content = resp.content
        else:
            raise HTTPNotAcceptable()

        if resp.encoding:
            doc_encoding = resp.encoding
            if doc_encoding.lower() != DEFAULT_ENCODING:
                try:
                    data = content.decode(doc_encoding, 'replace')
                except Exception:
                    raise HTTPNotAcceptable('Cannot decode requested content from advertized encoding: %s into unicode.' % doc_encoding)
                content = data.encode(DEFAULT_ENCODING)
                content = content.replace(doc_encoding, DEFAULT_ENCODING)

        response = Response(content, status=resp.status_code,
                            headers={'Content-Type': ct})

        return response
