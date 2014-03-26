# -*- coding: utf-8 -*-

import os
import sys
import optparse
import urlparse
import time
import codecs
from datetime import date
from optparse import OptionParser
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from boto.exception import DynamoDBResponseError

from chsdi.models.clientdata import ClientData
from chsdi.models.clientdata_dynamodb import get_table


if __name__ == '__main__':

    def parse_date(stringDate):
        try:
            dateInt = map(int, stringDate.split('-'))
            return date(dateInt[0], dateInt[1], dateInt[2])
        except:
            parser.print_help()
            sys.exit(1)

    def parse_url_params(url):
        ''' Malformed parts of the query string
        are dropped automatically
        '''
        # Drop urls containing the old techincal addresses
        if '.bgdi.admin.ch' in url:
            return None
        return dict(urlparse.parse_qsl(
            urlparse.urlparse(url).query
        ))

    def drop_re2_params(params):
        if 'selectedNode' in params:
            del params['selectedNode']
        if 'bgOpacity' in params:
            del params['bgOpacity']
        return params

    def build_qs_from_params(params):
        qs = ''
        for k, v in params.iteritems():
            qs += ''.join((k, '=', v, '&'))
        return qs[:-1]

    f = codecs.open('psql2dynamodb.log', 'w', 'utf-8')

    me = os.path.basename(sys.argv[0])

    epilog = '''Examples:

    Short links can be migrated using a date or date range filter (-d)

    1) Migrate all the links from postgresql to dynmaodb
    buildout/bin/python chsdi/scripts/pgsql2dynamodb.py -d all

    2) Migrate all the links created at a given date
    buildout/bin/python chsdi/scripts/pgsql2dynamodb.py -d 2014-02-20

    3) Migrate all the links in a date interval
    buildout/bin/python chsdi/scripts/pgsql2dynamodb.py -d 2014-02-20 2014-02-23
    \n'''

    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(epilog=epilog)
    parser.add_option('-d', '--date_filter', dest='date_filter', default=None, action='store', help='Filter by date(s)')

    (options, args) = parser.parse_args()

    if options.date_filter == 'all':
        dateFrom = None
        dateTo = None
        f.write('All entries selected\n')
    elif len(args) == 1:
        dateFrom = parse_date(options.date_filter)
        dateTo = parse_date(args[0])
        f.write('Select entries from %s to %s\n' % (str(dateFrom), str(dateTo)))
    elif len(args) > 1:
        parser.print_help()
        sys.exit(1)
    elif options.date_filter:
        dateFrom = parse_date(options.date_filter)
        dateTo = None
        f.write('Select entrie from %s until now\n' % (str(dateFrom)))

    engine = create_engine('postgresql://db1.bgdi.admin.ch:5432/clientdata')
    DBSession = scoped_session(sessionmaker())
    DBSession.configure(bind=engine)
    query = DBSession.query(ClientData)

    if dateFrom and dateTo is None:
        query = ClientData.filter_by_date(query, dateFrom)
    elif dateFrom and dateTo:
        query = ClientData.filter_by_daterange(query, dateFrom, dateTo)

    count = 0
    t0 = time.time()
    table = get_table()
    for q in query.yield_per(1000):
        # Parse url and clean permalink parameters
        url_parsed = parse_url_params(q.url)
        if url_parsed:
            host = q.url.split('?')[0]
            params = drop_re2_params(url_parsed)
            qs = build_qs_from_params(params)
            try:
                new_short_url = table.new_item(
                    hash_key=q.url_short,
                    attrs={
                        'url': host + '?' + qs,
                        'timestamp': str(q.bgdi_created)
                    })
                new_short_url.put()
                count += 1
            except DynamoDBResponseError as e:
                # print in log file
                f.write('An DynamoDB error occured while inserting the short URL %s\n' % q.url_short)
                f.write('Permalink is %s\n\n' % q.url)
        else:
            # Dropped URL
            f.write('Probably an old techincal address for the short URL %s\n' % q.url_short)
            f.write('Permalink is %s\n\n' % q.url)
        if count % 1000 == 0:
            tf = time.time()

    tf = time.time()
    f.write('It took %s seconds to migrate %s short URLs!' % (tf - t0, count))
    DBSession.close()
    f.close()
