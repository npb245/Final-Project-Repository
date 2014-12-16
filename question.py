import os
import urllib
import re
import datetime
import time
from email import utils
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db
from time import sleep
import jinja2
import webapp2
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Question(ndb.Model):
	author = ndb.UserProperty()
	content = ndb.StringProperty(indexed=False)
	tags = ndb.StringProperty(repeated=True)
	created = ndb.DateTimeProperty(auto_now_add=True)
	modified = ndb.DateTimeProperty(auto_now_add=True)
	votes = ndb.IntegerProperty(default=0)
	upVotes = ndb.StringProperty(repeated=True)
	downVotes = ndb.StringProperty(repeated=True)
		
class Answer(ndb.Model):
	author = ndb.UserProperty()
	q_id = ndb.KeyProperty()
	content = ndb.StringProperty(indexed=False)
	created = ndb.DateTimeProperty(auto_now_add=True)
	modified = ndb.DateTimeProperty(auto_now_add=True)
	votes = ndb.IntegerProperty(default=0)
	upVotes = ndb.StringProperty(repeated=True)
	downVotes = ndb.StringProperty(repeated=True)

class Image(ndb.Model):
	image = ndb.BlobProperty()
	author = ndb.UserProperty()
	link = ndb.StringProperty()

def truncateContent(str):
	return str[:500]

def hashTag(str):
	if str[0] == '#':
		return str[1:]
	else:
		return str	

def currentUser(author):
	if author == users.get_current_user():
		return True
	else:
		return False	

def notEmpty(tag):
	if str(tag).isspace():
		return False
	else:	
		return True	


def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

def datetimetorfc(value,len):
	nowtuple = value.timetuple()
	nowtimestamp = time.mktime(nowtuple)
	if len > 0:
		return utils.formatdate(nowtimestamp)[:-len]
	return utils.formatdate(nowtimestamp)

JINJA_ENVIRONMENT.filters['datetimeformat'] = datetimeformat
JINJA_ENVIRONMENT.filters['datetimetorfc'] = datetimetorfc
JINJA_ENVIRONMENT.filters['truncateContent'] = truncateContent
JINJA_ENVIRONMENT.filters['hashTag'] = hashTag
JINJA_ENVIRONMENT.tests['currentUser'] = currentUser
JINJA_ENVIRONMENT.tests['notEmpty'] = notEmpty

#Display Main page with list of questions
class MainPage(webapp2.RequestHandler):
	def get(self):
	
		q_query = Question.query().order(-Question.modified)
		que = q_query.fetch()

		paginator=Paginator(que, 10)

		page = self.request.get('page')
		try:
			q_page = paginator.page(page)
		except PageNotAnInteger:
	        # If page is not an integer, deliver first page.
			q_page = paginator.page(1)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			q_page = paginator.page(paginator.num_pages)

		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		template_values = {
			'questions': q_page,
			'url': url,
			'url_linktext': url_linktext,
			
        }
		
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


#Create new question
class CreateQuestion(webapp2.RequestHandler):
	def get(self):
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
			self.redirect(users.create_login_url(self.request.uri))
			
		
		template_values = {
			'url': url,
			'url_linktext': url_linktext,
        }
		template = JINJA_ENVIRONMENT.get_template('create.html')
		self.response.write(template.render(template_values))

#Upload new Image
class uploadImage(webapp2.RequestHandler):
	def get(self):
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
			self.redirect(users.create_login_url(self.request.uri))

		template_values = {
			'url': url,
			'url_linktext': url_linktext,
		}	
		template = JINJA_ENVIRONMENT.get_template('upload.html')
		self.response.write(template.render(template_values))

	def post(self):
		imageToUpload = Image()
		img=self.request.get('image')
		imageToUpload.image = db.Blob(img)
		imageToUpload.author = users.get_current_user()
		key = imageToUpload.put()

		logging.debug('IMG KEY=',str(imageToUpload.key.id()))
		self.redirect('/')

#Add question to datastore
class AddQuestion(webapp2.RequestHandler):
	def post(self):
		
		question = Question()
		if users.get_current_user():
			question.author = users.get_current_user()
		question.votes = 0
		question.content = self.request.get('content')
		tags = self.request.get('tags').split(',')
		tagx = []
		for tag in tags:
			tag2 = str(tag).lstrip()
			tag1 = str(tag2).rstrip()
			tagx.append(tag1)
			

		question.tags = tagx
		
		id = question.put()
		sleep(0.1)
		self.redirect('/')

#View questions based on tag
class ViewQuestionByTag(webapp2.RequestHandler):
	def get(self,tag):

		tag1 = str(tag)
		q_query = Question.query(Question.tags.IN([tag1])).order(-Question.modified)
		que = q_query.fetch()
		logging.debug('tag =%s|',tag1)
		logging.debug('que = %s',str(que))
		paginator=Paginator(que, 10)

		page = self.request.get('page')
		try:
			q_page = paginator.page(page)
		except PageNotAnInteger:
	        # If page is not an integer, deliver first page.
			q_page = paginator.page(1)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			q_page = paginator.page(paginator.num_pages)

		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		template_values = {
			'questions': q_page,
			'url': url,
			'url_linktext': url_linktext,
			
        }
		
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


#View images uploaded by current user
class ViewUploadedImages(webapp2.RequestHandler):
	def get(self):
		if users.get_current_user():
			url = users.create_logout_url('/')
			url_linktext = 'Logout'
			
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
		

		i_query = Image.query(Image.author == users.get_current_user())
		cursor = ndb.Cursor(urlsafe=self.request.get('cursor'))
		images = i_query.fetch() 
		next_c = None
		#images, next_curs, more = i_query.fetch_page(10, start_cursor=cursor) 
		
		for i in images:
			i.link = "/images/"+str(i.key.id())+".png"

		template_values = {
			'url': url,
			'url_linktext': url_linktext,
			'images': images,
			'cursor': next_c
		}
		
		template = JINJA_ENVIRONMENT.get_template('viewImages.html')
		self.response.write(template.render(template_values))


#View an image via permalink
class ViewImage(webapp2.RequestHandler):
	def get(self,image_id):
		img = re.findall(r'\d+',image_id)

		logging.debug('img= %s',str(img[0]))
		i_key = ndb.Key(Image,int(img[0]))

		imageToView = i_key.get()
		logging.debug('retrieved %s',imageToView)
		if image_id[-3:] in ['jpg','png','gif'] and imageToView is not None:
			wr = 'image/'+image_id[-3:]
			self.response.headers['Content-type'] = wr
			self.response.out.write(imageToView.image)
		else:
			logging.debug('NOT FOUND :(')
			self.response.headers['Content-type'] = 'text/html'
			self.response.out.write('Image Not Found')

#View a question via permalink		
class ViewQuestion(webapp2.RequestHandler):
	def get(self,q_id):
		
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
		
		
		
		question = self.request.get('quest')
		q_key = ndb.Key(Question,int(q_id))
		ques = q_key.get()
		expr = re.compile(r"(https?://[^ ]+(\.png|\.jpg|\.gif))")
		ques.content = expr.sub(r'<br><br><img src="\1" style="max-width:600px;"> <br>',ques.content)
		expr1 = re.compile(r"(?<!\")(https?://[^ ]+)")
		ques.content = expr1.sub(r'<a href="\1">\1</a>',ques.content)
	
		a_query = Answer.query(Answer.q_id == q_key).order(-Answer.votes)
		ans = a_query.fetch()
		for a in ans:
			a.content = expr.sub(r'<br><br><img src="\1" style="max-width:500px;"> <br>',a.content)
			a.content = expr1.sub(r'<a href="\1">\1</a>',a.content)

		paginator=Paginator(ans, 10)

		page = self.request.get('page')
		try:
			a_page = paginator.page(page)
		except PageNotAnInteger:
	        # If page is not an integer, deliver first page.
			a_page = paginator.page(1)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			a_page = paginator.page(paginator.num_pages)

		template_values = {
			'url': url,
			'url_linktext': url_linktext,
			'question': ques,
			'answers': a_page,
			
		}
		
		template = JINJA_ENVIRONMENT.get_template('viewq.html')
		self.response.write(template.render(template_values))



#Vote for a question	
class VoteQuestion(webapp2.RequestHandler):
	def get(self):
		question = self.request.get('quest')
		q_key = ndb.Key(urlsafe=question)
		ques = q_key.get()
		type = self.request.get('type')
		flag = 0
		if not users.get_current_user():
			self.redirect(users.create_login_url(self.request.uri))
		else:
			if ques.upVotes:
				if users.get_current_user().nickname() in ques.upVotes:
					flag = 1
			
			if ques.downVotes:
				if users.get_current_user().nickname() in ques.downVotes:
					flag = 2
			
			if flag == 0:
				if type == 'up':
					ques.upVotes.append(users.get_current_user().nickname())
				elif type == 'down':
					ques.downVotes.append(users.get_current_user().nickname())
			elif flag == 1:
				if type == 'down':
					ques.upVotes.remove(users.get_current_user().nickname())
					ques.downVotes.append(users.get_current_user().nickname())
			elif flag == 2:
				if type == 'up':
					ques.downVotes.remove(users.get_current_user().nickname())
					ques.upVotes.append(users.get_current_user().nickname())		
				
			ques.votes = len(ques.upVotes) - len(ques.downVotes)
			ques.put()
			sleep(0.1)
			redir_url = 'view/'+str(ques.key.id())
			self.redirect(redir_url)

#Vote for an answer		
class VoteAnswer(webapp2.RequestHandler):
	def get(self):
		answer = self.request.get('ans')
		a_key = ndb.Key(urlsafe=answer)
		ans = a_key.get()
		type = self.request.get('type')
		flag = 0
		
		if not users.get_current_user():
			self.redirect(users.create_login_url(self.request.uri))
		else:
			if ans.upVotes:
				if users.get_current_user().nickname() in ans.upVotes:
					flag = 1
			
			if ans.downVotes:
				if users.get_current_user().nickname() in ans.downVotes:
					flag = 2
			
			if flag == 0:
				if type == 'up':
					ans.upVotes.append(users.get_current_user().nickname())
				elif type == 'down':
					ans.downVotes.append(users.get_current_user().nickname())
			elif flag == 1:
				if type == 'down':
					ans.upVotes.remove(users.get_current_user().nickname())
					ans.downVotes.append(users.get_current_user().nickname())
			elif flag == 2:
				if type == 'up':
					ans.downVotes.remove(users.get_current_user().nickname())
					ans.upVotes.append(users.get_current_user().nickname())		
				
			ans.votes = len(ans.upVotes) - len(ans.downVotes)
			logging.debug('votes = ',str(ans.votes))
			ans.put()
			sleep(0.1)
			redir_url = 'view/'+str(ans.q_id.id())
			self.redirect(redir_url)

#Add answer for a question		
class AddAnswer(webapp2.RequestHandler):
	def post(self):
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			logging.debug("value of in users ",users.get_current_user)
			answer = Answer()
			
			answer.author = users.get_current_user()
			test = self.request.get('content')
				
			answer.content = self.request.get('content')
			id = self.request.get('q_id')
			answer.q_id = ndb.Key(urlsafe=id)
			id1 = answer.put()
			sleep(0.1)
			redir_url = 'view/'+str(answer.q_id.id())

			self.redirect(redir_url)

		else:
			logging.debug("Not in users")
			id = self.request.get('q_id')
			id1 = ndb.Key(urlsafe=id)
			redir_url = 'view/'+str(id1.q_id.id())

			self.redirect(users.create_login_url(redir_url))
			
#Edit a question			
class editQuestion(webapp2.RequestHandler):
	def get(self):
		question = self.request.get('quest')
		q_key = ndb.Key(urlsafe=question)
		ques = q_key.get()
		if users.get_current_user():
			if users.get_current_user() == ques.author:
				tags = ','.join(ques.tags)	
				
				template_values = {
					'question': ques,
					'tags': tags
				}
				
				template = JINJA_ENVIRONMENT.get_template('editq.html')
				self.response.write(template.render(template_values))
			else:
				redir_url = 'view/'+str(ques.key.id())
				self.redirect(redir_url)
		else:	
			self.redirect(users.create_login_url(self.request.uri))
			
	def post(self):
		question = self.request.get('quest')
		q_key = ndb.Key(urlsafe=question)
		ques = q_key.get()
		ques.content = self.request.get('content')
		tags = self.request.get('tags').split(',')
		
		tagx = []
		for tag in tags:
			tag2 = str(tag).lstrip()
			tag1 = str(tag2).rstrip()
			tagx.append(tag1)
			

		ques.tags = tagx
		ques.modified = datetime.datetime.now()
		ques.put()
		sleep(0.1)
		redir_url = 'view/'+str(ques.key.id())
		self.redirect(redir_url)

#Edit an answer
class editAnswer(webapp2.RequestHandler):
	def get(self):
		answer = self.request.get('ans')
		a_key = ndb.Key(urlsafe=answer)
		ans = a_key.get()
		if users.get_current_user():
			if users.get_current_user() == ans.author:
				template_values = {
					'answer': ans,
					
				}
				template = JINJA_ENVIRONMENT.get_template('editans.html')
				self.response.write(template.render(template_values))
			else:
				redir_url = 'view/'+str(ans.q_id.id())
				self.redirect(redir_url)
		else:	
			self.redirect(users.create_login_url(self.request.uri))
	
	def post(self):
		answer = self.request.get('ans')
		a_key = ndb.Key(urlsafe=answer)
		ans = a_key.get()
		ans.content = self.request.get('content')
		ans.modified = datetime.datetime.now()
		ans.put()
		sleep(0.1)
		redir_url = 'view/'+str(ans.q_id.id())
		self.redirect(redir_url)

#Generate RSS feed for a question
class GenerateRSS(webapp2.RequestHandler):
	"""docstring for GenerateRSS"""
	def get(self):
		q_id = self.request.get('ques')
		q_key = ndb.Key(Question,int(q_id))
		ques = q_key.get()
		
		a_query = Answer.query(Answer.q_id == q_key)
		ans = a_query.fetch()

		link = self.request.host_url + '/view/' + str(q_id)

		template_values = {
			'question': ques,
			'answers': ans,
			'link': link, 
		}
				
		template = JINJA_ENVIRONMENT.get_template('rss.xml')
		self.response.headers['Content-type']='text/xml'
		self.response.write(template.render(template_values))

	
application = webapp2.WSGIApplication([
    ('/', MainPage),
	('/create.html',CreateQuestion),
	('/upload.html',uploadImage),
	('/viewUploadedImages',ViewUploadedImages),
	('/addquestion',AddQuestion),
	('/addanswer',AddAnswer),
	('/voteq',VoteQuestion),
	('/voteans',VoteAnswer),
	('/editquestion',editQuestion),
	('/editanswer',editAnswer),
	('/generateRSS',GenerateRSS),
	(r'/view/(\d+)',ViewQuestion),
	(r'/images/(.*)',ViewImage),
	(r'/tags/(.*)',ViewQuestionByTag),
], debug=True)