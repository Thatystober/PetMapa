import sys
from os import path
from random import choice
from random import randint
sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, check_error_msg


class NotFound(Page):
    def __init__(self):
        Page.__init__(self, "not_found", html_file="not_found/index", bypass=False, public=True)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Algo estranho aconteceu", "page_name_val": "SWR"})
        check_error_msg(html, error_msg)
        if randint(1, 2) == 1:
            html.esc("case_type_val", "dog")
        else:
            html.esc("case_type_val", "cat")
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        return self.get(event, path, post, error_msg, user)
