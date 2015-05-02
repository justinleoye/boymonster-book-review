#!/usr/bin/env python
#-*- coding: utf-8 -*-
import sae
import web
#import urllib
import urllib2
import json
import datetime

from sqlalchemy import desc,distinct,or_

from acount import AcountHandler
from setting import render
from setting import load_sqla
from models import User, SchoolMajor, Book, UserBook, OrderList, BookReview

import re
import cgi
import random
import string
import hashlib
import copy
#
#valid useful functions
#
#escape the html
def escape_html(s):
    return cgi.escape(s, quote = True)


USERID_RE = re.compile(r"^[0-9]{1,11}$")
def valid_userid(userid):
    userid = str(userid)
    if userid:
        return USERID_RE.match(userid)

# use the re to check if the isbn is valided
ISBN_RE = re.compile(r"^\d{10}$|^\d{13}$")
SCHOOL_RE = re.compile(r"^[0-9]{1,2}$")
MAJOR_RE = re.compile(r"^[0-9]{6}$")
GRADE_RE = re.compile(r"^[0-9]$")
DISCOUNT_RE = re.compile(r"^[0-9]$")
EXTRA_RE = re.compile(r"^\w{0,120}$")#I just cann't do this job

TITLE_RE = re.compile(r"^\w{1,50}$")

USERBOOKID_RE = re.compile(r"^[0-9]*$")

def valid_isbn(isbn):
    if isbn:
        return ISBN_RE.match(isbn)
def valid_doubanid(doubanid):
    return True

def make_doubanid_isbn_hash(doubanid, isbn):
    return hashlib.sha256(doubanid + isbn).hexdigest()
    
def valid_order(doubanid, isbn, doubanid_isbn_hash):
    if valid_isbn(isbn) and valid_doubanid(doubanid):
        if doubanid_isbn_hash == make_doubanid_isbn_hash(doubanid, isbn):
            return True
            
    return False

def make_userbook_order_hash(userbookid,salt):
    return hashlib.sha256(str(userbookid) + str(salt)).hexdigest()

def valid_userbook_order(userbookid,salt,userbook_order_hash):
    if valid_userbookid(userbookid):
        if userbook_order_hash == make_userbook_order_hash(userbookid,salt):
            return True

    return False

def valid_school(school):
    if school:
        return SCHOOL_RE.match(school)

def valid_major(major):
    if major:
        return MAJOR_RE.match(major)

def valid_grade(grade):
    if grade:
        return GRADE_RE.match(grade)

def valid_discount(discount):
    if discount:
        return DISCOUNT_RE.match(discount)

def valid_extra(extra):
    #extra = str(extra)
    if len(extra)<=20:
        return True
    else:
        return False

def valid_title(title):
    if title:
        if len(title) <=90:
            return True
        else:
            return False

def valid_userbookid(userbookid):
    if userbookid:
        return USERBOOKID_RE.match(userbookid)

def get_price(price):
    Price_format = '0123456789.'
    for c in price:
        if not c in Price_format:
            price = price.replace(c,'')
    return price



#search a book info by douban book api
def isbn_search(isbn):
    url='https://api.douban.com/v2/book/isbn/%s?apikey=0b59cd1afb666b68220d6750f2334238' % (isbn)
    
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        html = response.read()
        data = json.loads(html)
        if data.has_key('id'):
            #something fuck here
            isbn = '%s' % (isbn)
            data['isbn'] = isbn
            data['price'] = get_price(data['price'])
            return data
        else:
            #just find no a book in douban
            return {'search-error':'242'}
    except (urllib2.HTTPError,urllib2.URLError), e:
        return {'search-error':str(e)}
# book search engine by douban api
def name_search(book_title):
    
    url="https://api.douban.com/v2/book/search?count=100&q=%s&apikey=0b59cd1afb666b68220d6750f2334238" % (book_title)
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        html = response.read()
        data = json.loads(html)
        if data.has_key('count'):
            if data['count'] ==0:
                return {'search-error':'242'}
            return data
        else:
            return {'search-error':'242'}
    except (urllib2.HTTPError,urllib2.URLError), e:
        return {'search-error':str(e)}

def match_search(books):
    in_books = []
    books_with_review = []
    if books.has_key('books'):
        for book in books['books']:
            in_book = web.ctx.orm.query(Book).filter(Book.doubanid==book['id']).first()
            if in_book:
                book['isbn']=in_book.isbn
                in_books.append(book)

            if book.has_key('isbn10') and book.has_key('isbn13'):
                book_with_review = web.ctx.orm.query(BookReview).filter(or_(BookReview.isbn==book['isbn10'], BookReview.isbn==book['isbn13'])).first()
            elif book.has_key('isbn10'):
                book_with_review = web.ctx.orm.query(BookReview).filter(BookReview.isbn==book['isbn10']).first()

            if book_with_review:
                book['isbn'] = book_with_review.isbn
                books_with_review.append(book)

    return {'books_on_sale': in_books, 'books_with_review': books_with_review}


#def search(book_title):
    #if valid_title(book_title):
        #books = name_search(book_title)
        #if not books.has_key('search-error'):
             #return match_search(books)
        #else:
            #return [books['search-error']]
    #else:
        #return ['624'] # not a valid title for search

def book_isbn_search(isbn):
    if valid_isbn(isbn):
        book=isbn_search(isbn)
        if not book.has_key('search-error'):
            is_in = web.ctx.orm.query(Book).filter_by(isbn=isbn).first()
            if is_in:
                return book
            else:
                book['search-error'] = '604'
                return book #book exists in douban ,but not exist in our db
        else:
            #just find no a book in douban
            return {'search-error':'242'}
    else:
        #just find no a book in douban
        return {'search-error':'608'} #not a valided isbn

def users_isbn_search(isbn,request):
    if valid_isbn(isbn):
        req0=request
        req1=req0+8
        users = web.ctx.orm.query(UserBook,User).filter(UserBook.userid==User.userid).filter(UserBook.isbn==isbn).order_by(desc(UserBook.date))[req0:req1]
        if users:
            return users
        else:
            return None

def users_book_isbn_search(isbn):
    if valid_isbn(isbn):
        users_book = web.ctx.orm.query(UserBook).filter(UserBook.isbn==isbn).order_by(desc(UserBook.date)).all()
        if users_book:
            return users_book
        else:
            return None

def user_book_isbn_search(isbn,userid):
    if valid_isbn(isbn):
        user_book = web.ctx.orm.query(UserBook).filter(UserBook.userid==userid).filter(UserBook.isbn==isbn).first()
        if user_book:
            return user_book
        else:
            return None

def user_books_search(userid,request):
    if valid_userid(userid):
        req0=request
        req1=req0+8
        user_books = web.ctx.orm.query(UserBook).filter(UserBook.userid==userid).order_by(desc(UserBook.date))[req0:req1]
        if user_books:
            return user_books
        else:
            return None

def get_user_other_user_books(userid,request):
    if valid_userid(userid):
        req0=request
        req1=req0+4
        user_books = web.ctx.orm.query(UserBook).filter(UserBook.userid==userid).order_by(desc(UserBook.date))[req0:req1]
        
        if user_books:
            return user_books
        else:
            return None

def classify_search(major,grade,request):
    if valid_major(major) and valid_grade(grade):
        req0=request
        req1=req0+8
        books = web.ctx.orm.query(distinct(UserBook.isbn)).filter(UserBook.major==major).filter(UserBook.grade==grade).order_by(desc(UserBook.date))[req0:req1]
        if books:
            return books
        else:
            return None

#some useful funcs for outer operations
def get_free_books_login(userid,request):
    if valid_userid(userid):
        req0=request
        req1=req0+7
        free_user_books = web.ctx.orm.query(UserBook).filter(UserBook.discount=='0').order_by(desc(UserBook.date))[req0:req1]
        if free_user_books:
            free_books=[]
            for free_user_book in free_user_books:
                book = book_isbn_search(free_user_book.isbn)
                if not book.has_key('search-error'):
                    is_in_orderlist = web.ctx.orm.query(OrderList).filter(OrderList.userbookid==free_user_book.userbookid).filter(OrderList.userid==userid).first()
                    if is_in_orderlist:
                        book['ordered']='True'
                    else:
                        book['ordered']='False'
                    book['ownerid']=free_user_book.userid
                    book['userbookid']=free_user_book.userbookid
                    free_books.append(book)
            return free_books
        else:
            return None
def get_free_books(request):
    req0=request
    req1=req0+7
    free_user_books = web.ctx.orm.query(UserBook).filter(UserBook.discount=='0').order_by(desc(UserBook.date))[req0:req1]
    if free_user_books:
        free_books=[]
        for free_user_book in free_user_books:
            book = book_isbn_search(free_user_book.isbn)
            if not book.has_key('search-error'):
                book['ordered']='False'
                book['ownerid']=free_user_book.userid
                book['userbookid']=free_user_book.userbookid
                free_books.append(book)
        return free_books
    else:
        return None
                

def get_orderlist(userid,request):
    if valid_userid(userid):
        req0=request
        req1=req0+8
        orderlist = web.ctx.orm.query(UserBook,OrderList).filter(OrderList.userbookid==UserBook.userbookid).filter(OrderList.userid==userid).order_by(desc(OrderList.date))[req0:req1]
        if orderlist:
            return orderlist
        else:
            return None









class Handler:
    def redirect(self,path):
        web.seeother(path)


class BookHandler(AcountHandler):
    def write_html(self, user=None, book={}, booksellers=[], search_error=''):
        return render.book(user=user, book=book, booksellers=booksellers, search_error=search_error)
        
    def GET(self,isbn):
        user=self.valid()

        isbn = isbn
        #verify the inputs
        valided_isbn = valid_isbn(isbn)

        isbn_error = ''
        book={}
        search_error='200'

        if not valided_isbn:
            isbn_error = "That's not a valid ISBN.Don't kidding!"

        if isbn_error == '':
            
            book = book_isbn_search(isbn)
            booksellers=[]
            if not book.has_key('search-error'):
                if user:
                    book_user = user_book_isbn_search(isbn,user.userid)
                    if book_user:
                        book['owner'] = 'True'
                book_users = users_isbn_search(isbn,0)
                if book_users:
                    for b_u,b_user in book_users:
                        bookseller={}
                        bookseller['userbookid'] = b_u.userbookid
                        bookseller['username'] = b_user.username
                        bookseller['date'] = b_u.date
                        bookseller['discount'] = b_u.discount
                        bookseller['major'] = get_major_name(b_u.major)
                        bookseller['grade'] = get_grade_name(b_u.grade)
                        bookseller['extra'] = b_u.extra
                        bookseller['userid'] = b_user.userid
                        booksellers.append(bookseller)
                
                #no sellers but book exsits in Book database
                if booksellers==[]:
                    web.ctx.orm.query(Book).filter(Book.isbn==isbn).delete()
                    
                return self.write_html(user,book,booksellers,search_error)
            elif book['search-error'] == '604':
                search_error = book['search-error']
                return self.write_html(user=user,book=book,search_error=search_error)
            elif book['search-error'] == '242':
                book['wrong-isbn']=isbn
                search_error = book['search-error']
                return self.write_html(user=user,book=book,search_error=search_error)
        else:
            search_error='608'
            return self.write_html(user=user,search_error=search_error)

class BuyHandler(AcountHandler):
    def write_html(self, user=None):
        return render.buybook(user=user)

    def GET(self,userid):
        #query the database and return the info of the book
        #display the info of the book owner
        self.redirect('/user/%s' % (userid))
        

class SellHandler(AcountHandler):
    def write_html(self, user=None, isbn='', book={}, booksellers=[], isbn_error='', search_error=''):
        return render.sellbook(user=user, isbn=isbn, book=book, booksellers=booksellers, isbn_error=isbn_error, search_error=search_error)

    def GET(self):
        # if the user is valided
        user = self.valid()
        #if not user:
            #self.redirect('/login')
        return self.write_html(user)

    def POST(self):
        #return the info of the in-selling book input by valided user
        user=self.valid()
        #if not user:
            #self.redirect('/login')
        #
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
            if not book.has_key('search-error'):
                book_users = users_isbn_search(isbn,0)
                if book_users:
                    for b_u,b_user in book_users:
                        bookseller={}
                        bookseller['userbookid'] = b_u.userbookid
                        bookseller['username'] = b_user.username
                        bookseller['date'] = b_u.date
                        bookseller['discount'] = b_u.discount
                        bookseller['major'] = get_major_name(b_u.major)
                        bookseller['grade'] = get_grade_name(b_u.grade)
                        bookseller['extra'] = b_u.extra
                        bookseller['userid'] = b_user.userid
                        booksellers.append(bookseller)
                return self.write_html(user,isbn,book,booksellers,isbn_error,search_error)
            else:
                search_error=book['search-error']
                return self.write_html(user=user,isbn=isbn,book=book,isbn_error=isbn_error,search_error=search_error)
        else:
            return self.write_html(user=user,isbn=isbn,book=book,isbn_error=isbn_error)

            
        #query and push into the db
        #return the operation info

class FinishSellHandler(AcountHandler):
    def write_html(self,user=None, const_info={}, book={}, search_error=''):
        return render.finishsell(user=user, const_info=const_info, book=book, search_error=search_error)

    def GET(self,isbn):
        #return the info of the in-selling book input by valided user
        user=self.valid()
        #
        const_info = copy.deepcopy(CONST_INFO)
        search_error='200'
        book = isbn_search(isbn)
        
        if not book.has_key('search-error'):
            doubanid_isbn_hash = make_doubanid_isbn_hash(book['id'], isbn)
            book['hash'] = doubanid_isbn_hash
            return self.write_html(user,const_info,book,search_error)
        else:
            search_error=book['search-error']
            return self.write_html(user,const_info,book,search_error)

    def POST(self,isbn):

        #valid the current user's validation
        user = self.valid()
        if not user:
            return self.redirect('/login')
        i = web.input()
        school = i.school
        doubanid = i.doubanid
        hashkey = i.hashkey
        isbn = i.isbn
        school = i.school
        major = i.major
        grade = i.grade
        discount = i.discount
        extra = i.extra

        valided_order = valid_order(doubanid,isbn,hashkey)
        valided_school = valid_school(school)
        valided_major = valid_major(major)
        valided_grade = valid_grade(grade)
        valided_discount = valid_discount(discount)
        valided_extra = valid_extra(extra)
        

        order_error = ''
        school_error = ''
        major_error = ''
        grade_error = ''
        discount_error = ''
        extra_error = ''

        if not valided_order:
            order_error = 'order is not valided'
        if not valided_school:
            school_error = 'school select wrong'
        if not valided_major:
            major_error = 'major select wrong'
        if not valided_grade:
            grade_error = 'grade select wrong'
        if not valided_discount:
            discount_error = 'discount select wrong'
        if not valided_extra:
            extra_error = 'this text is limited under 20 words'

        if order_error == '' and school_error == '' and major_error == '' and grade_error == '' and discount_error == '' and extra_error == '':
            book = web.ctx.orm.query(Book).filter_by(doubanid=doubanid).first()
            if not book:
                b = Book(
                    doubanid = doubanid,
                    isbn = isbn
                )
                web.ctx.orm.add(b)

            userbook = web.ctx.orm.query(UserBook).filter_by(userid=user.userid,isbn=isbn).first()
            if not userbook:
                ub = UserBook(
                    userid = user.userid,
                    isbn = isbn,
                    major = major,
                    grade = grade,
                    discount = discount,
                    extra = extra
                )
                web.ctx.orm.add(ub)
                
                return self.redirect('/book/%s' % (isbn)) 
            else:
                search_error='600' # the user has already sell this book before
                return self.write_html(user=user,search_error=search_error)
        else:
            const_info = copy.deepcopy(CONST_INFO)
            search_error='610' #the extra input overflow
            book = isbn_search(isbn)

            const_info = copy.deepcopy(CONST_INFO)
            const_info['default']['school']=school
            const_info['default']['major']=major
            const_info['default']['grade']=grade
            const_info['default']['discount']=discount
            const_info['default']['extra']=extra
            #return const_info['default']
            if not book.has_key('search-error'):
                doubanid_isbn_hash = make_doubanid_isbn_hash(book['id'], isbn)
                book['hash'] = doubanid_isbn_hash
                return self.write_html(user,const_info,book,search_error)
            else:
                search_error=book['search-error']
                return self.write_html(user,const_info,book,search_error)

class DelHandler(AcountHandler):
    def write_html(self, user=None, book={}, user_book=None, search_error=''):
        return render.delbook(user=user, book=book, user_book=user_book, search_error=search_error)

    def GET(self,isbn):
        #if the user is valided and the del action is verified
        #if the user is valided
        user=self.valid()

        if not user:
            return self.redirect('/login')

        search_error='200'
        book = isbn_search(isbn)
        if not book.has_key('search-error'):
            #check the user's authority
            user_book = user_book_isbn_search(isbn,user.userid)
            if user_book:
                doubanid_isbn_hash = make_doubanid_isbn_hash(book['id'], isbn)
                book['hash'] = doubanid_isbn_hash
                return self.write_html(user,book,user_book,search_error)
            else:
                #the current user has no authority to edit this book
                search_error='612'
                return self.write_html(user=user,book=book,search_error=search_error)
        else:
                search_error=book['search-error'] 
                return self.write_html(user=user,search_error=search_error)

    def POST(self,isbn):
        #valid the current user's validation
        user = self.valid()
        if not user:
            return self.redirect('/login')

        #check the user's authority
        user_book = user_book_isbn_search(isbn,user.userid)
        if user_book:
            i = web.input()
            doubanid = i.doubanid
            hashkey = i.hashkey
            isbn = i.isbn

            valided_order = valid_order(doubanid,isbn,hashkey)

            order_error = ''

            if not valided_order:
                order_error = 'order is not valided'

            if order_error == '':
                web.ctx.orm.query(OrderList).filter(OrderList.userbookid==user_book.userbookid).delete()
                web.ctx.orm.delete(user_book)
                users_book = users_book_isbn_search(isbn)
                if not users_book:
                    #if this delete action is from the last seller,then delete this book in the Book table
                    book = web.ctx.orm.query(Book).filter_by(isbn=isbn).first()
                    if book:
                        web.ctx.orm.delete(book)
                        self.redirect('/me')
                self.redirect('/me')
            else:
                search_error = '614' # the post delete order just wrong
                return self.write_html(user=user,search_error=search_error)
                    

class EditHandler(AcountHandler):
    def write_html(self, user=None, book={}, user_book=None, const_info={}, search_error=''):
        return render.editbook(user=user, book=book, user_book=user_book, const_info=const_info, search_error=search_error)

    def GET(self,isbn):
        #if the user is valided
        user=self.valid()
        if not user:
            return self.redirect('/login')

        search_error='200'
        book = isbn_search(isbn)

        if not book.has_key('search-error'):
            user_book = user_book_isbn_search(isbn,user.userid)
            if user_book:
                doubanid_isbn_hash = make_doubanid_isbn_hash(book['id'], isbn)
                book['hash'] = doubanid_isbn_hash
                const_info = copy.deepcopy(CONST_INFO)
                const_info['default']['school']=get_school_by_major(user_book.major)
                const_info['default']['major']=user_book.major
                const_info['default']['grade']=user_book.grade
                
                return self.write_html(user,book,user_book,const_info,search_error)
            else:
                search_error='612' #the current user has no authority to edit this book
                return self.write_html(user=user,search_error=search_error)
        else:
            search_error=book['search-error']
            return self.write_html(user=user,search_error=search_error)

    def POST(self,isbn):
        #if the user is valided
        #user=self.valid()
        #i = web.input()
        #return the edited info of the book input by valided user
        #verify the inputs
        #query and update into the db
        #return the operation info
        #valid the current user's validation
        user = self.valid()
        if not user:
            return self.redirect('/login')

        #check the user's authority
        user_book = user_book_isbn_search(isbn,user.userid)
        if user_book:
            i = web.input()
            school = i.school
            doubanid = i.doubanid
            hashkey = i.hashkey
            isbn = i.isbn
            school = i.school
            major = i.major
            grade = i.grade
            discount = i.discount
            extra = i.extra
    
            valided_order = valid_order(doubanid,isbn,hashkey)
            valided_school = valid_school(school)
            valided_major = valid_major(major)
            valided_grade = valid_grade(grade)
            valided_discount = valid_discount(discount)
            valided_extra = valid_extra(extra)
            
    
            order_error = ''
            school_error = ''
            major_error = ''
            grade_error = ''
            discount_error = ''
            extra_error = ''
    
            if not valided_order:
                order_error = 'order is not valided'
            if not valided_school:
                school_error = 'school select wrong'
            if not valided_major:
                major_error = 'major select wrong'
            if not valided_grade:
                grade_error = 'grade select wrong'
            if not valided_discount:
                discount_error = 'discount select wrong'
            if not valided_extra:
                extra_error = 'this text is limited under 20 words'
    
            if order_error == '' and school_error == '' and major_error == '' and grade_error == '' and discount_error == '' and extra_error == '':
                user_book.major = major
                user_book.grade = grade
                user_book.discount = discount
                user_book.extra = extra
                user_book.date = datetime.datetime.now()
                
                web.ctx.orm.add(user_book)
                
                return self.redirect('/book/%s' % (isbn)) 
            else:
                search_error='610' #the extra input overflow
                book = isbn_search(isbn)
                
                if not book.has_key('search-error'):
                    doubanid_isbn_hash = make_doubanid_isbn_hash(book['id'], isbn)
                    book['hash'] = doubanid_isbn_hash
                    return self.write_html(user,book,user_book,search_error)
                else:
                    search_error=book['search-error']
                    return self.write_html(user,book,user_book,search_error)

            #search_error = '634' #select inputs are not valided
        else:
            search_error='612' # the user has no authority to edit this book
            return self.write_html(user=user,search_error=search_error)

class MeHandler(AcountHandler):
    def write_html(self, user=None, u_books=None, search_error=''):
        return render.me(user=user, u_books=u_books, search_error=search_error)

    def GET(self):
        #valid the user
        user = self.valid()

        search_error = '200'
        if user:
            user_books = user_books_search(user.userid,0)
            u_books=[]
            if user_books:
                for user_book in user_books:
                    book=book_isbn_search(user_book.isbn)
                    if not book.has_key('search-error'):
                        u_books.append(book)
                    
                return self.write_html(user,u_books,search_error)
            else:
                search_error = '618' #this user has sell no book
                return self.write_html(user,u_books,search_error)

        else:
            self.redirect('/login')

class OrderListHandler(AcountHandler):
    def write_html(self, user=None, order_list=None):
        return render.orderlist(user=user, order_list=order_list)

    def GET(self):
        user = self.valid()
        if user:
            search_error='200'
            order_list = []
            orderlist = get_orderlist(user.userid,0)
            if orderlist:
                for order_userbook,order in orderlist:
                    order_book = {}
                    book = isbn_search(order_userbook.isbn)
                    
                    if not book.has_key('search-error'):
                        order_book['title']=book['title']
                        order_book['images']=book['images']
                        order_book['price']=book['price']
                        order_book['isbn']=order_userbook.isbn
                        order_book['ownerid']=order_userbook.userid
                        order_book['userbookid']=order_userbook.userbookid
                        order_book['discount']=order_userbook.discount
                        order_book['date']=order.date
                        order_list.append(order_book)
                return self.write_html(user,order_list)
            if  order_list==[]:
                search_error='644' #no order in this user's orderlist
                return self.write_html(user,order_list)
        else:
            self.redirect('/login')

class OrderHandler(AcountHandler):
    def write_html(self, user=None, userbook=None, search_error=''):
        return render.order(user=user, userbook=userbook, search_error=search_error)

    def GET(self,userbookid):
        user = self.valid()

        userbookid = userbookid
        search_error='200'
        if valid_userbookid(userbookid):
            user_book = web.ctx.orm.query(UserBook).filter(UserBook.userbookid==userbookid).first()
            if not user_book:
                search_error = '642' #there is not a sell relation in the database
                return self.write_html(user=user,search_error=search_error)
            else:
                userbook={}
                userbook['userbookid']=user_book.userbookid
                userbook['ownerid']=user_book.userid
                userbook['ordered']='False' #user not login or logined user has not this order before
                if user:
                    orderlist = web.ctx.orm.query(OrderList).filter(OrderList.userid == user.userid).filter(OrderList.userbookid == userbookid).first()
                    if orderlist:
                        userbook['ordered']='True'# logined user has this order already
                #userbook['hash']=make_userbook_order_hash(user_book.userbookid,userbookid)
                return self.write_html(user,userbook,search_error)
        else:
            search_error = '640' #the userbookid is not valided
            return self.write_html(user=user,search_error=search_error)
    def POST(self,userbookid):
        user = self.valid()
        userbookid = userbookid
        
        if user:
            i = web.input()
            #hashkey = i.hashkey
            i_userbookid = i.userbookid

            if valid_userbookid(userbookid) and str(userbookid)==str(i_userbookid):
                orderlist = web.ctx.orm.query(OrderList).filter(OrderList.userid == user.userid).filter(OrderList.userbookid == userbookid).first()
                if not orderlist:
                    order = OrderList(
                        userid = user.userid,
                        userbookid = userbookid
                    )
                    web.ctx.orm.add(order)
                else:
                    web.ctx.orm.delete(orderlist)
                return 'True'
            return 'False'
        else:
            return 'NotLogin'


class SearchHandler(AcountHandler):
    def write_html(self, user=None, result={}, search_error=''):
        return render.search(user=user, result=result, search_error=search_error)

    def GET(self,p):
        user = self.valid()
        
        search_error = '200'
        result ={}
        if p:
            p=p.encode('UTF-8')#this is a brilliant time for my coding
    
            if valid_title(p):
                d_books = name_search(p)
                if not d_books.has_key('search-error'):
                    result = match_search(d_books)
                    if len(result['books_on_sale'])==0 and len(result['books_with_review'])==0:
                        search_error = '626' #book not exist in our inner db
                else:
                    search_error = d_books['search-error']
            else:
                search_error = '624' # not a valid title for search
        else:
            search_error = '624' #not a valided title for search

        return self.write_html(user, result, search_error)

    def POST(self):
        user =self.valid
        i = web.input()
        self.redirect('/search/%s' % (i.keyword))

class ClassifyHandler(AcountHandler):
    def write_html(self, user=None, const_info={}, books=[], search_error=''):
        return render.classify(user=user, const_info=const_info, books=books, search_error=search_error)

    def GET(self):
        user = self.valid()

        const_info = copy.deepcopy(CONST_INFO)
        return self.write_html(user,const_info)
    def POST(self):
        user = self.valid()

        i = web.input()
        school = i.school
        major = i.major
        grade = i.grade

        valided_school = valid_school(school)
        valided_major = valid_major(major)
        valided_grade = valid_grade(grade)

        school_error = ''
        major_error = ''
        grade_error = ''

        search_error = '200'
        books = []
        const_info = copy.deepcopy(CONST_INFO)

        if not valided_school:
            school_error = 'school select wrong'
        if not valided_major:
            major_error = 'major select wrong'
        if not valided_grade:
            grade_error = 'grade select wrong'

        if school_error == '' and major_error == '' and grade_error =='':
            in_books = classify_search(major,grade,0)
            const_info['default']['school']=school
            const_info['default']['major']=major
            const_info['default']['grade']=grade
            #return in_books
            if in_books:
                i = 0
                for in_book in in_books:
                    i+=1
                    book = isbn_search(in_book)
                    if not book.has_key('search-error'):
                        books.append(book)
                if i == 0:
                    search_error = '632' # no book specified by major and grade in the inner database
                    return self.write_html(user,const_info,books,search_error)

                if books:
                    return self.write_html(user,const_info,books,search_error)
                else:
                    search_error = '630' #complex error,check it by backtracing the funcs
                    return self.write_html(user,const_info,books,search_error)
            else:
                search_error = '632' # no book specified by major and grade in the inner database
                return self.write_html(user,const_info,books,search_error)
        else:
            search_error = '634' #select inputs are not valided

class AjaxPager(AcountHandler):
    def GET(self,keyword,request):
        result = self.get_result(keyword,request)
        return result

    #/me,/classify,/book/**,/sellbook
    def get_result(self,keyword,request):
        user = self.valid()
        if keyword == 'me' and user:
            request=int(request)
            user_books =user_books_search(user.userid,request)
            u_books=[]
            if user_books:
                for user_book in user_books:
                    book=book_isbn_search(user_book.isbn)
                    u_books.append(book)
            return json.dumps(u_books)
        elif keyword == 'classify':
            request,major,grade=request.split('&')
            request = int(request)
            books = []
            in_books = classify_search(major,grade,request)

            if in_books:
                i = 0
                for in_book in in_books:
                    i+=1
                    book = isbn_search(in_book)
                    if not book.has_key('search-error'):
                        books.append(book)
                if i == 0:
                    search_error = '632' # no book specified by major and grade in the inner database
                    return json.dumps([])

                if books:
                    return json.dumps(books)
                else:
                    search_error = '630' #complex error,check it by backtracing the funcs
                    return json.dumps([])
            else:
                search_error = '632' # no book specified by major and grade in the inner database
                return json.dumps([])

        elif keyword == 'book':
            request,isbn = request.split('&')
            request = int(request)
            booksellers = []
            if valid_isbn(isbn):
                book = isbn_search(isbn)
                if book:
                    book_users = users_isbn_search(isbn,request)
                    if book_users:
                        for b_u,b_user in book_users:
                            bookseller={}
                            bookseller['username'] = b_user.username
                            bookseller['date'] = b_u.date.strftime("%Y-%m-%d")
                            bookseller['discount'] = float(b_u.discount) *0.1*float(book['price'])
                            bookseller['major'] = get_major_name(b_u.major)
                            bookseller['grade'] = get_grade_name(b_u.grade)
                            bookseller['extra'] = b_u.extra
                            bookseller['userid'] = b_user.userid
                            booksellers.append(bookseller)
                    return json.dumps(booksellers)
                else:
                    return json.dumps([])
        elif keyword == 'freebook':
            user = self.valid()

            request=int(request)
            if user:
                free_books = get_free_books_login(user.userid,request)
            else:
                free_books = get_free_books(request)
            if free_books:
                return json.dumps(free_books)
            else:
                return json.dumps([])
        elif keyword == 'acount':
            user = self.valid()
            if request == 'logincheck':
                if user:
                    result = 'True'
                else:
                    result = 'False'
                return result
            else:
                return None
        else:
            return None
            

class InfoMajorHandler(Handler):
    def get_major(self,school):
        school = str(school)
        major = SCHOOLMAJOR_JSON[school]
        # some no needed data tranceaction,I should rewrite it later by javascript
        html=''
        for i in range(len(major)):
            if i==0:
                html+='<option value="%s" selected="selected">%s</option>' % (major[i][0],major[i][1])
            else:
                html+='<option value="%s">%s</option>' % (major[i][0],major[i][1])
        return html
    def GET(self,school):
        if valid_school(school):
            return self.get_major(school)


#some const info
SCHOOL_JSON=[['0',u'材料科学与工程学院'],['1',u'地球与环境学院'],['2',u'能源与安全学院'],['3',u'土木建筑学院'],['4',u'机械工程学院'],['5',u'电气与信息工程学院'],['6',u'化学工程学院'],['7',u'测绘学院'],['8',u'理学院'],['9',u'外国语学院'],['10',u'经济与管理学院'],['11',u'人文社会科学学院'],['12',u'医学院'],['13',u'计算机科学与工程学院'],['99',u'全  校  通  用']]
SCHOOLMAJOR_JSON={
    '0':[['080203',u'无机非金属材料工程'],['080103',u'矿物加工工程'],['080204',u'高分子材料与工程'],['080206',u'复合材料与工程'],['080210',u'再生资源科学与技术'],['000000',u'材料学院通用']],
    '1':[['080106',u'地质工程'],['080104',u'勘查技术与工程'],['081001',u'环境工程'],['080802',u'水文与水资源工程'],['071403',u'自然地理与资源环境'],['000001',u'地环学院通用']],
    '2':[['080101',u'采矿工程'],['081002',u'安全工程'],['000002',u'能源学院通用']],
    '3':[['080703',u'土木工程'],['080704',u'建筑环境与设备工程'],['110104',u'工程管理'],['080701',u'建筑学'],['080706',u'城市地下空间工程'],['080708',u'景观建筑设计'],['000003',u'土木学院通用']],
    '4':[['080301',u'机械设计制造及其自动化'],['080401',u'测控技术及仪器'],['080303',u'工业设计'],['080304',u'过程装备与控制工程'],['080306',u'车辆工程'],['000004',u'机械学院通用']],
    '5':[['080602',u'自动化'],['080603',u'电子信息工程'],['080604',u'通信工程'],['080601',u'电气工程及其自动化'],['000005',u'电气学院通用']],
    '6':[['081603',u'弹药工程与爆炸技术'],['081101',u'化学工程与工艺'],['081102',u'制药工程'],['070302',u'应用化学'],['081604',u'特种能源技术与工程'],['081106',u'能源化学工程'],['000006',u'化工学院通用']],
    '7':[['080901',u'测绘工程'],['070703',u'地理信息系统'],['080902',u'遥感科学与技术'],['000007',u'测绘学院通用']],
    '8':[['070101',u'数学与应用数学'],['070102',u'信息与计算科学'],['070202',u'应用物理学'],['071101',u'理论与应用力学'],['081702',u'工程结构分析'],['081701',u'工程力学'],['000008',u'理学院通用']],
    '9':[['050201',u'英语专业'],['000009',u'外国语学院通用']],
    '10':[['020104',u'金融学'],['110102',u'信息管理与信息系统'],['110202',u'市场营销'],['110205',u'人力资源管理'],['110209',u'电子商务'],['020115',u'环境资源与发展经济学'],['000010',u'经管学院通用']],
    '11':[['030401',u'政治学与行政学'],['050418',u'动画本科专业'],['000011',u'人文学院通用']],
    '12':[['100301',u'临床医学专业'],['100304',u'医学检验专业'],['100701',u'护理学专业'],['100201',u'预防医学专业'],['100801',u'药学专业'],['000012',u'医学院通用']],
    '13':[['080605',u'计算机科学与技术专业'],['071205',u'信息安全专业'],['080402',u'电子信息技术及仪器'],['080640',u'物联网工程'],['000013',u'计算机学院通用']],
    '99':[['111111',u'全校通用']]
}
GRADE_JSON=[['0',u'大 一'],['1',u'大 二'],['2',u'大 三'],['3',u'大 四'],['4',u'大 五'],['5',u'考 研'],['9',u'通 用']]

DEFAULT_SCHOOL_MAJOR_GRADE ={'school':'0','major':'0','grade':'0','discount':'3','extra':''}

CONST_INFO={'school':SCHOOL_JSON,'schoolmajor':SCHOOLMAJOR_JSON,'grade':GRADE_JSON,'default':DEFAULT_SCHOOL_MAJOR_GRADE}

def get_school_by_major(major):
    for school_code,school in SCHOOLMAJOR_JSON.items():
        for major_code,major_name in school:
            if major_code == major:
                return school_code

    return '0'

def get_major_list_num(major):
    for school_code,school in SCHOOLMAJOR_JSON.items():
        for i in range(len(school)):
            if school[i][0]==major:
                return str(i)

    return '0'

def get_major_name(majorcode):
    for school_code,school in SCHOOLMAJOR_JSON.items():
        for major_code,major_name in school:
            if major_code == majorcode:
                return major_name

    return u'无机非金属材料工程'

def get_grade_name(gradecode):
    code = int(gradecode)
    if code==9:
        code = 6 #it is just temperary strategy
    if code <10:
        return GRADE_JSON[code][1]
    else:
        return u'大 一'





