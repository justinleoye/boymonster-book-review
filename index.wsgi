#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os

import sae
import web

import copy

from setting import render
from setting import load_sqla
from acount import get_user
from models import User, SchoolMajor, Book, UserBook
from acount import AcountHandler,SignupHandler,LoginHandler,LogoutHandler,WelcomeHandler,ProfileHandler,EditProfileHandler,DelAcountHandler
from book import BookHandler,BuyHandler,SellHandler,FinishSellHandler,DelHandler,EditHandler,MeHandler,OrderListHandler,OrderHandler,SearchHandler,ClassifyHandler,AjaxPager,InfoMajorHandler,CONST_INFO,get_free_books_login,get_free_books,get_user_other_user_books,isbn_search
from book_review import BookReviewHandler, BookReviewsHandler, CheckBookHandler, AddBookReviewHandler, EditBookReviewHandler
# the urls of the web system
urls = (
    '/(.*)/', 'RedirectHandler',
    '/', 'HomeHandler',
    '/home','HomeHandler',
    '/me','MeHandler',
    '/orderlist','OrderListHandler',
    '/user/([0-9]*)','UserHandler',
    '/about','AboutHandler',
    '/contact','ContactHandler',
    '/terms','TermsHandler',
    '/help','HelpHandler',
    '/signup','SignupHandler',
    '/login','LoginHandler',
    '/logout','LogoutHandler',
    '/welcome','WelcomeHandler',
    '/profile','ProfileHandler',
    '/editprofile','EditProfileHandler',
    '/delacount','DelAcountHandler',
    '/search/(.*)','SearchHandler',#there are some flaws here
    '/search','SearchHandler',
    '/classify','ClassifyHandler',
    '/book/([0-9]*)','BookHandler',
    '/buybook/([0-9]*)','BuyHandler',
    '/order/([0-9]*)','OrderHandler',
    '/sellbook','SellHandler',
    '/finishsell/(\d{10}|\d{13})','FinishSellHandler',
    '/delbook/([0-9]*)','DelHandler',
    '/editbook/([0-9]*)','EditHandler',
    '/info/getmajor/([0-9]{1,2})','InfoMajorHandler',
    '/ajaxpager/(.*)/([0-9]{1,2}|[0-9]{1,2}[&][0-9]{6}[&][0-9]|[0-9]{1,2}[&][0-9]{10}|[0-9]{1,2}[&][0-9]{13}|logincheck)','AjaxPager',
    '/checkbook','CheckBookHandler',
    '/addbookreview/([0-9]*)', 'AddBookReviewHandler',
    '/book/([0-9]*)/reviews', 'BookReviewsHandler',
    '/book/([0-9]*)/reviews/([0-9]*)', 'BookReviewHandler',
    '/book/([0-9]*)/reviews/([0-9]*)/action/edit', 'EditBookReviewHandler',
)


#access the database
#db = web.database(dbn='mysql', db='alexbox', user='root', pw='alexzone')

class Handler:
    def redirect(self,path):
        web.seeother(path)

#when the url ended with '/',then redirect the url to the one without ending '/'
class RedirectHandler(Handler):
    def GET(self, path):
        self.redirect('/' + path)

class HomeHandler(AcountHandler):
    def write_html(self, user=None, const_info={}, free_books=None):
        return render.home(user=user, const_info=const_info, free_books=free_books)

    def GET(self):
        user=self.valid()
        const_info = copy.deepcopy(CONST_INFO)

        if user:
            free_books = get_free_books_login(user.userid,0)
        else:
            free_books = get_free_books(0)
        return self.write_html(user, const_info, free_books)

    def POST(self):
        user = self.valid()

        i = web.input()
        
class UserHandler(AcountHandler):
    def write_html(self,user=None, owner=None, owner_books=[], search_error=''):
        return render.user(user=user, owner=owner, owner_books=owner_books, search_error=search_error)

    def GET(self,userid):
        user=self.valid()
        owner = get_user(userid)

        search_error = '200'
        if not owner:
            search_error='616' #user not found

        if owner:
            owner_books=[]
            owner_user_books=get_user_other_user_books(owner.userid,0)
            if owner_user_books:
                for owner_user_book in owner_user_books:
                    owner_book={}
                    book = isbn_search(owner_user_book.isbn)
                    if not book.has_key('search-error'):
                        owner_book['title']=book['title']
                        owner_book['images']=book['images']
                        owner_book['isbn']=book['isbn']

                        owner_books.append(owner_book)
            if owner_books == []:
                search_error='646' #owner has no other books.

            return self.write_html(user,owner,owner_books,search_error)
        return self.write_html(user=user,owner=owner,search_error=search_error)

    
class AboutHandler(AcountHandler):
    def write_html(self, user=None):
        return render.about(user=user)

    def GET(self):
        user=self.valid()
        return self.write_html(user)

class ContactHandler(AcountHandler):
    def write_html(self, user=None):
        return render.contact(user=user)
        
    def GET(self):
        user=self.valid()
        return self.write_html(user)

class TermsHandler(AcountHandler):
    def write_html(self, user=None):
        return render.terms(user=user)

    def GET(self):
        user=self.valid()
        return self.write_html(user)

class HelpHandler(AcountHandler):
    def write_html(self,user=None):
        return render.help(user=user)

    def GET(self):
        user = self.valid()

        return self.write_html(user)


#class Referer:
    #def GET(self):
        #referer = web.ctx.env.get('HTTP_REFERER','http://google.com')
        ##raise web.seeother(referer)
        ##return web.ctx.env
        ##return web.ctx.path
        ##return web.ctx.home
        ##return web.ctx.homedomain
        ##return web.ctx.status
        #return web.ctx.headers

app = web.application(urls, globals())
app.add_processor(load_sqla)

application = sae.create_wsgi_app(app.wsgifunc())

