import sys
from os import path

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html


class Donation(Page):
    def __init__(self):
        Page.__init__(self, "donation", html_file="donation/index", bypass=False, public=True)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Doação"})
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        return self.get(event, path, post, error_msg, user)
