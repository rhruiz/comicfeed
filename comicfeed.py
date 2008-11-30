import wsgiref.handlers
from google.appengine.ext import webapp
from controllers import feeds


def main():
	application = webapp.WSGIApplication(
		[
			('/', feeds.ShowFeed),
			('/feed', feeds.ShowFeed),
			('/show', feeds.ShowPage),
			('/enclosure', feeds.ShowEnclosure),
			('/fetch', feeds.FetchFeed),
		],
		debug=True)

	wsgiref.handlers.CGIHandler().run(application)


if __name__ == "__main__":
	main()
