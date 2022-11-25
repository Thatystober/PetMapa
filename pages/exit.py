import sys
from os import path

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, redirect, check_error_msg


class Exit(Page):
    def __init__(self):
        Page.__init__(self, "exit", html_file="exit/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        return redirect(""), "logout", user

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        return self.get(event, path, post, error_msg, user)
