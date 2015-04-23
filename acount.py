#!/usr/bin/env python
#-*- coding: utf-8 -*-
import sae
import web
import urllib
import re
import cgi
from setting import render

from setting import load_sqla
from models import User,UserBook,Book
#valid useful functions
def escape_html(s):
    return cgi.escape(s, quote = True)

USERID_RE = re.compile(r"^[0-9]{1,11}$")
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
TEL_RE = re.compile(r"^[0-9]{11}$")

def valid_userid(userid):
    userid = str(userid)
    if userid:
        return USERID_RE.match(userid)

def valid_name(name):
    if name:
        return USER_RE.match(name)

def valid_password(password):
    if password:
        return PASSWD_RE.match(password)

def verify_password(password, v_password):
    if v_password and password == v_password:
        return v_password

def valid_email(email):
    if email:
        return EMAIL_RE.match(email)

def valid_tel(tel):
    if tel:
        return TEL_RE.match(tel)






import random
import string
import hashlib

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

# Implement the function valid_pw() that returns True if a user's password 
# matches its hash. You will need to modify make_pw_hash.

def make_pw_hash(pw):
    salt = make_salt()
    h = hashlib.sha256(pw + salt).hexdigest()
    return '%s,%s' %(h,salt)

def valid_pw(pw_h):
    if pw_h:
        h = pw_h.split('|')
    else:
        return False
        
    #user = User.get_by_id(int(h[0]))
    user = web.ctx.orm.query(User).filter_by(username=h[0]).first()

    if user:
        if h[1] == user.userpass:
            return user
        else:
            return False
        
def verify_pw(pw,pw_h,salt):
    if pw and pw_h and salt:
        
        if pw_h == hashlib.sha256(pw + salt).hexdigest():
            return True

#some useful funcs
#get info of a user
def get_user(userid):
    #userid=str(userid)
    if valid_userid(userid):
        user = web.ctx.orm.query(User).filter_by(userid=userid).first()
        if user:
            return user
        else:
            return None

class AcountHandler:
    def redirect(self,path):
        web.seeother(path)
        
    def valid(self):
        cookie_user = web.cookies().get('user')
        user = valid_pw(cookie_user)
        if user:
            return user
        else:
            #delete the cookie
            web.setcookie('user','')
            return None

class SignupHandler(AcountHandler):
    def write_html(self,user=None, username='', email='', tel='', username_error='', password_error='', v_password_error='', email_error='',tel_error='', terms_error=''):
        return render.signup(user=user, username=username, email=email, tel=tel, username_error=username_error, password_error=password_error, v_password_error=v_password_error, email_error=email_error, tel_error=tel_error, terms_error=terms_error)
        
    def GET(self):
        user= self.valid()
        return self.write_html(user)

    def POST(self):
        i=web.input()
        username = i.username
        password = i.password
        v_password = i.verify
        email = i.email
        tel = i.tel
        try:
            terms = i.terms
        except: 
            terms = ''
        
        valided_username = valid_name(username)
        valided_password = valid_password(password)
        verified_password = verify_password(password, v_password)
        valided_email = valid_email(email)
        valided_tel = valid_tel(tel)

        username_error = ''
        password_error = ''
        v_password_error = ''
        email_error = ''
        tel_error = ''
        terms_error = ''

        if not valided_username:
            username_error = "That's not a valid username."

        if not valided_password:
            password_error = "That wasn't a valid password."
        elif not verified_password:
            v_password_error = "Your passwords didn't match."

        if not valided_email:
            email_error = "That's not a valid email."

        if not valided_tel:
            tel_error = "This is not a valid telephone number."
            
        if not terms:
            terms_error = "The terms not been checked"

        if username_error == '' and password_error == '' and v_password_error == '' and email_error == '' and tel_error=='' and terms_error == '':
            #Access the database and do something cool
            user = web.ctx.orm.query(User).filter_by(username=username).first()
            email_user = web.ctx.orm.query(User.email).filter_by(email=email).first()
            if not user and not email_user:
                h = (make_pw_hash(password)).split(',')
                pw_h = h[0]
                salt = h[1]
                u = User(
                    username = username,
                    userpass =pw_h,
                    salt =salt,
                    email =email,
                    tel = tel
                )
                web.ctx.orm.add(u)
                cookie_user = '%s|%s' % (username,pw_h)
                #set cookie
                web.setcookie('user',cookie_user)
                self.redirect('/welcome')
            else:
                if user:
                    username_error = u'该用户名已经被使用！'
                    user=None
                if email_user:
                    email_error = u'该邮箱已经注册过，不能重复注册！'
                    email_user=None
                return self.write_html(user=user, username=username,tel=tel, username_error = username_error, email_error = email_error)

        else:
            username = escape_html(username)
            email = escape_html(email)
            user=None
            return self.write_html(user,username, email, tel, username_error, password_error, v_password_error, email_error, tel_error, terms_error)
            

class LoginHandler(AcountHandler):
    def write_html(self,user=None, error=''):
        return render.login(user=user, error=error)

    def GET(self):
        user = self.valid()
        return self.write_html(user)

    def POST(self):
        i = web.input()

        #username = i.username
        email = i.email
        password = i.password

        #valided_username = valid_name(username)
        valided_email = valid_email(email)
        valided_password = valid_password(password)
        
        if valided_email and valided_password:
            #validation success,access the database
            users = web.ctx.orm.query(User).filter_by(email=email).all()
            if users:
                user = users[0]
                userid = user.userid

                if verify_pw(password, user.userpass, user.salt):
                    cookie_user = '%s|%s' % (user.username, user.userpass)
                    #set cookie
                    web.setcookie('user',cookie_user)
                    self.redirect('/welcome')
            else:
                return self.write_html(user=None, error='The user is not exist,or the password does not match this acount!oops!')

        else:
            return self.write_html(user=None, error='The input name or password is invalid!oops!')

class LogoutHandler(AcountHandler):
    def GET(self):
        #delete the cookie
        web.setcookie('user','')
        self.redirect('/login')

class WelcomeHandler(AcountHandler):
    def write_html(self, user=None):
        return render.welcome(user=user)

    def GET(self):
        user = self.valid()
        if user:
            return self.write_html(user)
        else:
            self.redirect('/login')
        
class ProfileHandler(AcountHandler):
    def write_html(self,user=None):
        return render.profile(user=user)

    def GET(self):
        user = self.valid()
        if user:
            return self.write_html(user)
        else:
            self.redirect('/login')

class EditProfileHandler(AcountHandler):
    def write_html(self,user=None,email='',tel='',email_error='',tel_error=''):
        return render.editprofile(user=user, email=email, tel=tel, email_error=email_error, tel_error=tel_error)

    def GET(self):
        user = self.valid()
        if user:
            email = user.email
            tel = user.tel
            return self.write_html(user,email,tel)
        else:
            self.redirect('/login')

    def POST(self):
        user = self.valid()
        if user:
            i = web.input()
            email = i.email
            tel = i.tel

            valided_email = valid_email(email)
            valided_tel = valid_tel(tel)

            email_error = ''
            tel_error = ''

            if not valided_email:
                email_error = u'您输入的email有错误！'

            if not valided_tel:
                tel_error = u'您输入的手机号有错误！'

            if email_error == '' and tel_error == '':
                user.email = email
                user.tel = tel

                self.redirect('/profile')

            else:
                return self.write_html(user,email,tel,email_error,tel_error)
        else:
            self.redirect('/login')

        

class DelAcountHandler(AcountHandler):
    def write_html(self,user=None):
        return render.delacount(user=user)

    def GET(self):
        user = self.valid()
        if user:
            return self.write_html(user)
        else:
            self.redirect('/login')

    def POST(self):
        user = self.valid()
        if user:
            i = web.input()
            delacount = i.delacount
    
            if delacount == '1':
                user_books = web.ctx.orm.query(UserBook).filter(UserBook.userid == user.userid).delete()
                web.ctx.orm.delete(user)

                self.redirect('/home')
            else:
                self.redirect('/delacount')
        else:
            self.redirect('/login')











    
