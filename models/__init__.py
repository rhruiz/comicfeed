from google.appengine.ext import db
import datetime

class Feed(db.Model):
	name = db.StringProperty(multiline=False)
	url = db.StringProperty()
	active = db.BooleanProperty()
	last_updated = db.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def get_active_feeds():
		feeds = db.GqlQuery("select * from Feed where active = :1", True)
		return feeds
	

	@staticmethod
	def init():
		feed_count = db.GqlQuery("select * from Feed").count()
		if feed_count == 0:
			feed = Feed()
	                feed.name = "Explosm"
	                feed.url = "http://feeds.feedburner.com/Explosm"
	                feed.active = True
			feed.last_updated = datetime.datetime.fromtimestamp(0)
	                feed.put()


class FeedItem(db.Model):
	url = db.StringProperty()
	title = db.StringProperty()
	content = db.TextProperty()
	date  = db.DateTimeProperty(auto_now_add=True)
	enclosure = db.BlobProperty()
	feed = db.ReferenceProperty(Feed)
	content_type = db.StringProperty()

	@staticmethod
	def is_fetched(url):
		items = db.GqlQuery("select * from FeedItem where url = :1", url)
		return items.count() > 0

	@staticmethod
	def get_latest():
		items = db.GqlQuery("select * from FeedItem order by date desc limit 10")
		return items
