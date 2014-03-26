# -*- coding: utf-8 -*-

from sqlalchemy import Column, Text
from sqlalchemy.types import Date, DateTime
from sqlalchemy.sql.expression import cast

from chsdi.models import bases

Base = bases['clientdata']


class ClientData(Base):
    __tablename__ = 'shorturl'
    __table_args__ = ({'schema': 'chsdi', 'autoload': False})
    url_short = Column('url_short', Text, primary_key=True)
    url = Column('url', Text)
    bgdi_created = Column('bgdi_created', DateTime)

    @classmethod
    def filter_by_date(cls, query, dateFrom):
        return query.filter(cast(cls.bgdi_created, Date) == str(dateFrom))

    @classmethod
    def filter_by_daterange(cls, query, dateFrom, dateTo):
        return query.filter(cast(cls.bgdi_created, Date).between(str(dateFrom), str(dateTo)))
