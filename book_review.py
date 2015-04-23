#!/usr/bin/env python
#-*- coding: utf-8 -*-
import sae
import web
#import urllib
import urllib2
import json
import datetime

from sqlalchemy import desc,distinct

from acount import AcountHandler,get_user
from book import isbn_search, valid_isbn
from setting import render
from setting import load_sqla
from models import User, BookReview

import re
import cgi
import random
import string
import hashlib
import copy
#
#valid useful functions
def valid_content(content):
    if content != None and len(content)>12:
        return True
    return False

USERBOOKID_RE = re.compile(r"^[0-9]*$")

def valid_review_id(id):
    if id:
        return USERBOOKID_RE.match(id)
    return False
#
#escape the html
def escape_html(s):
    return cgi.escape(s, quote = True)

class Handler:
    def redirect(self,path):
        web.seeother(path)

def get_book_reviews(request):
    req0=request
    req1=req0+8
    book_reviews = web.ctx.orm.query(BookReview).order_by(desc(BookReview.updated))[req0:req1]
    if book_reviews:
        for book_review in book_reviews:
            writer = get_user(book_review.userid)
            book_review.writer = writer
        return book_reviews
    else:
        return None

def get_book_review(review_id):
    book_review = web.ctx.orm.query(BookReview).filter(BookReview.id==review_id).first()
    return book_review

class BookReviewsHandler(AcountHandler):
    def write_html(self, user=None, book={}, book_reviews=[], isbn_error='', search_error=''):
        return render.book_reviews(user=user, book=book, book_reviews=book_reviews, isbn_error=isbn_error, search_error=search_error)

    def GET(self,isbn):
        user=self.valid()

        isbn = isbn
        #verify the inputs
        valided_isbn = valid_isbn(isbn)

        isbn_error = ''
        book={}
        book_reviews = []
        search_error='200'

        if not valided_isbn:
            isbn_error = "That's not a valid ISBN.Don't kidding!"

        if isbn_error == '':
            book = isbn_search(isbn)
            if not book.has_key('search-error'):
                book_reviews = web.ctx.orm.query(BookReview).filter(BookReview.isbn==isbn).order_by(desc(BookReview.updated)).all()
                for book_review in book_reviews:
                    writer = get_user(book_review.userid)
                    book_review.writer = writer
            else:
                search_error=book['search-error']
        return self.write_html(user, book, book_reviews, isbn_error, search_error)

class CheckBookHandler(AcountHandler):
    def write_html(self, user=None, isbn='', book={}, isbn_error='', search_error=''):
        return render.check_book(user=user, isbn=isbn, book=book, isbn_error=isbn_error, search_error=search_error)

    def GET(self):
        # if the user is valided
        user = self.valid()
        return self.write_html(user)

    def POST(self):
        #return the info of the in-selling book input by valided user
        user=self.valid()
        i = web.input()
        isbn = i.isbn
        
        #verify the inputs
        valided_isbn = valid_isbn(isbn)

        isbn_error = ''
        book={}
        search_error='200'

        if not valided_isbn:
            isbn_error = u"您输入的ISBN格式不正确。"

        if isbn_error == '':
            
            book = isbn_search(isbn)
            booksellers=[]
            if book.has_key('search-error'):
                search_error=book['search-error']
        return self.write_html(user=user,isbn=isbn,book=book,isbn_error=isbn_error,search_error=search_error)

class BookReviewHandler(AcountHandler):
    def write_html(self, user=None, book={}, review='',  isbn_error='', search_error='', content_error=''):
        return render.book_review(user=user, book=book, review=review, isbn_error=isbn_error, search_error=search_error, content_error=content_error)

    def GET(self, isbn, review_id):
        user = self.valid()

        #verify the inputs
        valided_isbn = valid_isbn(isbn)
        valided_review_id = valid_review_id(review_id)

        isbn_error = ''
        book={}
        search_error='200'
        review = None

        if not valided_isbn:
            isbn_error = "That's not a valid ISBN.Don't kidding!"
        if not valided_review_id:
            review_id_error = "That's not a valid review.Don't be kidding!"

        if valided_isbn and valided_review_id:
            book = isbn_search(isbn)
            if not book.has_key('search-error'):
                review = get_book_review(review_id)
                writer = get_user(review.userid)
                review.writer = writer
                try:
                    if user.userid == review.userid:
                        review.isOwned = True
                    else:
                        review.isOwned = False
                except (KeyError), e:
                    print e
            else:
                search_error=book['search-error']
        return self.write_html(user=user, book=book, review=review, isbn_error=isbn_error, search_error=search_error)

class AddBookReviewHandler(AcountHandler):
    def write_html(self, user=None, book={}, content='',  isbn_error='', search_error='', content_error=''):
        return render.add_book_review(user=user, book=book, content=content, isbn_error=isbn_error, search_error=search_error, content_error=content_error)

    def GET(self, isbn):
        user = self.valid()

        if not user:
            return self.redirect('/login')

        #verify the inputs
        valided_isbn = valid_isbn(isbn)

        isbn_error = ''
        book={}
        search_error='200'

        if not valided_isbn:
            isbn_error = "That's not a valid ISBN.Don't kidding!"

        if isbn_error == '':
            book = isbn_search(isbn)
            if book.has_key('search-error'):
                search_error=book['search-error']
        return self.write_html(user=user, book=book, isbn_error=isbn_error, search_error=search_error)

    def POST(self, isbn):
        user = self.valid()
        if not user:
            return self.redirect('/login')
        i = web.input()
        isbn = i.isbn
        content = i.content

        #verify the inputs
        valided_isbn = valid_isbn(isbn)
        valided_content = valid_content(content)

        isbn_error = ''
        content_error = ''
        book={}
        search_error='200'

        if not valided_isbn:
            isbn_error = "That's not a valid ISBN.Don't be kidding!"
        if not valided_content:
            content_error = "The book review content should be more than 12 words."

        book = isbn_search(isbn)
        print 'book:',book
        if not book.has_key('search-error'):
            if isbn_error == '' and content_error == '':
                br = BookReview(
                    isbn = isbn,
                    userid = user.userid,
                    content = content,
                    updated = datetime.datetime.now()
                )
                web.ctx.orm.add(br)
                return self.redirect('/book/%s/reviews' % (isbn))
        else:
            search_error=book['search-error']
        return self.write_html(user, book, content, isbn_error, search_error, content_error)

class EditBookReviewHandler(AcountHandler):
    def write_html(self, user=None, book={}, review='',  isbn_error='', search_error='', content_error=''):
        return render.edit_book_review(user=user, book=book, review=review, isbn_error=isbn_error, search_error=search_error, content_error=content_error)

    def GET(self, isbn, review_id):
        user = self.valid()

        #verify the inputs
        valided_isbn = valid_isbn(isbn)
        valided_review_id = valid_review_id(review_id)

        isbn_error = ''
        book={}
        search_error='200'
        review = None

        if not valided_isbn:
            isbn_error = "That's not a valid ISBN.Don't kidding!"
        if not valided_review_id:
            review_id_error = "That's not a valid review.Don't be kidding!"

        if valided_isbn and valided_review_id:
            book = isbn_search(isbn)
            if not book.has_key('search-error'):
                review = get_book_review(review_id)
            else:
                search_error=book['search-error']
        return self.write_html(user=user, book=book, review=review, isbn_error=isbn_error, search_error=search_error)

    def POST(self, isbn, review_id):
        user = self.valid()
        if not user:
            return self.redirect('/login')
        i = web.input()
        content = i.content

        #verify the inputs
        valided_isbn = valid_isbn(isbn)
        valided_review_id = valid_review_id(review_id)
        valided_content = valid_content(content)

        isbn_error = ''
        review_id_error = ''
        content_error = ''
        review = {'content': content, 'id': review_id}
        book={}
        search_error='200'

        if not valided_isbn:
            isbn_error = "That's not a valid ISBN.Don't be kidding!"
        if not valided_review_id:
            review_id_error = "That's not a valid review.Don't be kidding!"
        if not valided_content:
            content_error = "The book review content should be more than 12 words."

        if valided_isbn and valided_review_id and valided_content:
            book = isbn_search(isbn)
            if not book.has_key('search-error'):
                br = get_book_review(review_id)
                if br:
                    br.content = content
                    br.updated = datetime.datetime.now()
                    web.ctx.orm.add(br)
                    return self.redirect('/book/%s/reviews/%s' % (isbn, review_id))
                else:
                    review_id_error = 'Book review not found'
            else:
                search_error=book['search-error']
        return self.write_html(user, book, review, isbn_error, search_error, content_error)
