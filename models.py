#!/usr/bin/env python
#-*- coding: utf-8 -*-
import sae
import web

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String , Text , DateTime


Base = declarative_base()

class User(Base):
    __tablename__='user'

    userid = Column(Integer, primary_key = True)
    username = Column(String(20))
    userpass = Column(String(100))
    salt = Column(String(100))
    email = Column(String(100))
    tel = Column(String(11))

class SchoolMajor(Base):
    __tablename__='schoolmajor'

    schoolid = Column(Integer)
    majorid = Column(Integer, primary_key = True)

class Book(Base):
    __tablename__='book'
    
    bookid = Column(Integer, primary_key=True)
    doubanid = Column(String(20))
    isbn = Column(String(13))# not so sure

class UserBook(Base):
    __tablename__='userbook'

    userbookid = Column(Integer, primary_key=True)
    userid = Column(Integer)
    isbn = Column(String(13))
    major = Column(String(6))
    grade = Column(String(1))
    discount = Column(Integer)
    extra = Column(String(240))
    date = Column(DateTime)

class OrderList(Base):
    __tablename__='orderlist'

    orderid = Column(Integer, primary_key=True)
    userid = Column(Integer)
    userbookid = Column(Integer)
    date = Column(DateTime)

class BookReview(Base):
    __tablename__='book_review'

    id = Column(Integer, primary_key=True)
    isbn = Column(String(13))# not so sure
    content = Column(Text) 
    userid = Column(Integer)
    created = Column(DateTime)
    updated = Column(DateTime)
