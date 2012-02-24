import logging
import feedparser
import time
import datetime
import re
import templates
from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.ext import db
from models import Feed, FeedItem

class ShowEnclosure(webapp.RequestHandler):
	def get(self):
		if self.request.get("id"):
			item = FeedItem.get_by_id(int(self.request.get("id")))
			if item:
				if 'content_type' not in item.__dict__:
					item.content_type = 'image/png'
					item.put()

				self.response.headers["Content-Type"] = item.content_type
				self.response.out.write(item.enclosure)
			else:
				self.redirect("/assets/hello.jpg")
		else:
			self.redirect("/assets/hello.jpg")

class ShowAbstract(webapp.RequestHandler):
        def _updateFeeds(self):
                logging.debug("ShowFeed::_updateFeeds()")
                ctrl = FetchFeed()
                ctrl.initialize(self.request, self.response)
                ctrl.get()

        def _init(self):
                logging.debug("ShowFeed::_init()")
                feeds = Feed.get_active_feeds()
                if feeds:
                    for feed in feeds:
                        if time.time() - time.mktime(datetime.datetime.timetuple(feed.last_updated)) >= 3600*4:
                                logging.debug("Feed '%s' Triggered feed update" % feed.name)
                                self._updateFeeds()
                                break
                
		
		self.items = FeedItem.get_latest()
		logging.debug("Got %d feed items" % self.items.count())

class ShowPage(ShowAbstract):
	def get(self):
		self._init()
		self.response.out.write(templates.render_template('latest.html', { 'items': self.items }))

class ShowFeed(ShowAbstract):
	def get(self):
		self._init()
		self.response.out.write(templates.render_template('latest.rss', { 'items':  self.items }))

class FetchFeed(webapp.RequestHandler):

	def _init(self):
		Feed.init()

	def _getFeeds(self):
		feeds = Feed.get_active_feeds()
		if not feeds or feeds.count() == 0:
			logging.debug("Got no active feeds, initializing data")
			self._init()
			return self._getFeeds()

		return feeds


	def get(self):
		feeds = self._getFeeds()
		logging.debug("Got %d feeds" % feeds.count())
		for feed in feeds:
			logging.debug("Feed %s last updated %s" % (feed.name, feed.last_updated))
			force = self.request.get("force") == "1"
			if force:
				logging.debug("Force option enabled")

			if not force and time.time() - time.mktime(datetime.datetime.timetuple(feed.last_updated)) < 3600*4:
				logging.debug("Feed %s doesn't need updates, skipping" % feed.name)
				continue

			logging.debug("Fetching %s" % feed.url)
			feed_content = urlfetch.fetch(feed.url)
			logging.debug("Fetched, status = %d" % feed_content.status_code)
			if feed_content.status_code == 200:
				parsed_feed = feedparser.parse(feed_content.content)
				feed.last_updated = datetime.datetime.now()
				feed.put()
			else:
				logging.error("Failed to load feed %s" % feed.name)
				self.error(500)
				
			linkre = re.compile("http://(?:www\.)?explosm.net/comics/\d+/?")
			comicre = re.compile('(http://(?:www\.)?explosm.net/db/files/Comics/[A-z0-9_\-\+]+/[A-z0-9\-_\+]+\.(gif|png))')
	
			logging.debug("Got %d entries" % len(parsed_feed.entries))
			for e in parsed_feed.entries:
				if linkre.match(e.link):
					if not FeedItem.is_fetched(e.link):
						logging.debug("Going to fetch entry %s" % e.link)
						result = urlfetch.fetch(e.link)
						logging.debug("Fetched, status = %d" % result.status_code)
						if result.status_code == 200:
							results = comicre.findall(result.content)
							if results and len(results) > 0:
								logging.debug("Going to fetch enclosure %s" % results[0][0])
								enclosure = urlfetch.fetch(results[0][0])
								logging.debug("Fetched, status = %d" % enclosure.status_code)
								if enclosure.status_code == 200:
									feed_item = FeedItem()
									feed_item.title = e.title
									feed_item.url = e.link
									feed_item.content_type = "image/"+results[0][1]
									feed_item.feed = feed
									feed_item.date = datetime.datetime.fromtimestamp(time.mktime(e.updated_parsed))
									feed_item.content = db.Text(e.description)
									feed_item.enclosure = enclosure.content
									feed_item.put()
								else:
									logging.error("Failed to fetch enclosure %s" % results[0])
								
							else:
								logging.debug("Got no enclosure in %s" % e.link)
	
						else:
							logging.debug("Failed to download %s" % e.link)
					else:
						logging.debug("Skipping already fetch item %s" % e.link)
				else:
					logging.debug("Skipping unknown link %s" % e.link)

