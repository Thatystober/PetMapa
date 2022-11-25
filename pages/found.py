import sys
from os import path

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, redirect, check_error_msg


class Found(Page):
    def __init__(self):
        Page.__init__(self, "found", html_file="found/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Encontrei"})
        check_error_msg(html, error_msg)
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if post.get("case_type"):
            if post["case_type"] == "dog":
                return redirect("found_model/dog")
            elif post["case_type"] == "cat":
                return redirect("found_model/cat")
        else:
            return self.get(event, path, post, "selecione se você encontrou um cachorro ou gato", user)
