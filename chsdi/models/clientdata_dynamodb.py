#-*- utf-8 -*-

import pyramid.httpexceptions as exc

import boto

'''
Create the table described hereunder.

import boto
conn=boto.connect_dynamodb()
schema=conn.create_schema(hash_key_name='url_short',hash_key_proto_value='S')
table=conn.create_table(name='shorturls', schema=schema, read_units=25, write_units=25)

Drop table.

import boto
conn=boto.connect_dynamodb()
table=conn.get_table('shorturls')
table.delete()

'''

# http://boto.readthedocs.org/en/latest/boto_config_tut.html


def get_table():

    # url_short is the pkey
    try:
        conn = boto.connect_dynamodb()
        return conn.get_table('shorturls')
    except Exception as e:
        raise exc.HTTPBadRequest('Error during connection %s' % e)
