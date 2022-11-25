import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, User, parse_html, redirect, check_error_msg, validate_password


class RegisterPassword(Page):
    def __init__(self):
        Page.__init__(self, "register_password", html_file="register_password/index", bypass=True, public=True)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "user_email" in path:
            return redirect("login")
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Cadastro"})
        html.esc("user_email_val", path["user_email"])
        check_error_msg(html, error_msg)
        if post.get("user_password"):
            html.esc("user_password_val", post["user_password"])
            html.esc("if_user_password_exists", "focus")
        if post.get("user_password_confirm"):
            html.esc("user_password_confirm_val", post["user_password_confirm"])
            html.esc("if_user_password_confirm_exists", "focus")
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "user_email" in path:
            return redirect("login")
        if not post.get("user_password"):
            return self.get(event, path, post, "verifique o campo senha", user)
        if not post.get("user_password_confirm"):
            return self.get(event, path, post, "verifique o campo confirme sua senha", user)
        if post["user_password"] != post["user_password_confirm"]:
            return self.get(event, path, post, "as senhas devem coincidir", user)
        if not validate_password(post["user_password"]):
            return self.get(event, path, post, "a senha escolhida é muito fraca, forneça uma senha maior", user)

        user = User(user_email=path["user_email"])
        user.load_information()
        user.user_valid = True
        user.user_password = post["user_password"]
        user.update_user()
        return "Register completed", "login", user
