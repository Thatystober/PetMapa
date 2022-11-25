import sys
from os import path

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, User, parse_html, validate_email, redirect, check_error_msg, encode_to_b64


class Login(Page):
    def __init__(self):
        Page.__init__(self, "login", html_file="login/index", bypass=True, public=True)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Login"})
        if not post:
            if path.get("login_message"):
                error_msg = "é necessário estar logado para acessar as demais funções"
        check_error_msg(html, error_msg)
        if post.get("user_email"):
            html.esc("user_email_val", post["user_email"])
            html.esc("if_user_email_exists", "focus")
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not post.get("user_email"):
            return self.get(event, path, post, "email inválido", user)
        if not validate_email(post["user_email"]):
            return self.get(event, path, post, "email inválido", user)
        user = User(user_email=post["user_email"])
        user.load_information()
        if user.user_valid:
            return redirect("password/" + encode_to_b64(post["user_email"]))
        else:
            return redirect("register/" + encode_to_b64(post["user_email"]))
