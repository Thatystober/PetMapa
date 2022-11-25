import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, redirect


class PasswordEmailSent(Page):
    def __init__(self):
        Page.__init__(self, "password_email_sent", html_file="password_email_sent/index", bypass=True, public=True)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("user_email"):
            return redirect("login")
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Esqueci minha senha"})
        html.esc("user_email_val", path["user_email"])
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        return self.get(event, path, post, error_msg, user)
