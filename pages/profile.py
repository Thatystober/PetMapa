import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, format_to_mobile_phone_number


class Profile(Page):
    def __init__(self):
        Page.__init__(self, "profile", html_file="profile/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Perfil"})
        html.esc("user_name_val", user.user_name.title())
        html.esc("user_email_val", user.user_email)
        html.esc("user_last_name_val", user.user_last_name.title())
        html.esc("user_phone_val", format_to_mobile_phone_number(user.user_phone))
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        return self.get(event, path, post, error_msg, user)
