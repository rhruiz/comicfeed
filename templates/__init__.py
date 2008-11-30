import os
from google.appengine.ext.webapp import template

def get_template_path(file):
	path = os.path.join(os.path.dirname(__file__), ('%s' % file))
	return path

def render_template(file, vars):
	path = get_template_path(file)
	return template.render(path, vars)
