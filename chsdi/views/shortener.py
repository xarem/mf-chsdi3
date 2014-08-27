#-*- utf-8 -*-

from pyramid.view import view_config
import pyramid.httpexceptions as exc

from urlparse import urlparse
import time

from chsdi.models.clientdata_dynamodb import get_table
from chsdi.lib.helpers import check_url


def _add_item(url):
    table = get_table()

    # Create a new short url if url not in DB
    t = int(time.time() * 1000) - 1000000000000
    url_short = '%x' % t
    try:
        new_url_short = table.new_item(
            hash_key=url_short,
            attrs={
                'url': url,
                'timestamp': time.strftime('%Y-%m-%d %X', time.localtime())
            })
        new_url_short.put()
    except Exception as e:
        raise exc.HTTPBadRequest('Error during put item %s' % e)
    return url_short


@view_config(route_name='shorten', renderer='jsonp')
def shortener(request):
    url = check_url(
        request.params.get('url')
    )
    url_short = _add_item(url)
    return {
        'shortUrl': ''.join((
                            's.geo.admin.ch/',
                            url_short
                            ))
    }


@view_config(route_name='shorten_redirect')
def shorten_redirect(request):
    url_short = request.matchdict.get('id')
    if url_short is None:
        raise exc.HTTPBadRequest('Please provide an id')
    table = get_table()
    try:
        url_short = table.get_item(url_short)
        url = url_short.get('url')
    except Exception as e:
        raise exc.HTTPBadRequest('This short url doesn\'t exist: s.geo.admin.ch/%s Error is: %s' % (url_short, e))
    raise exc.HTTPFound(location=url)
