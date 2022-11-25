import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, check_error_msg, parse_html, redirect, validate_password, put_user_password_into_crypto_data_base


class PasswordReset(Page):
    def __init__(self):
        Page.__init__(self, "password_reset", html_file="password_reset/index", bypass=False, public=True)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "user_email_token" in path:
            return redirect("")

        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Redefinir Senha"})
        check_error_msg(html, error_msg)
        html.esc("user_email_val", user.user_email)
        if post.get("user_password"):
            html.esc("user_password_val", post.get("user_password"))
            html.esc("if_user_password_exists", "focus")
        if post.get("user_password_confirm"):
            html.esc("user_password_confirm_val", post.get("user_password_confirm"))
            html.esc("if_user_password_confirm_exists", "focus")
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "user_email_token" in path:
            return redirect("login")

        if not post.get("user_password"):
            return self.get(event, path, post, "verifique o campo senha", user)
        if not post.get("user_password_confirm"):
            return self.get(event, path, post, "verifique o campo confirme sua senha", user)
        if post["user_password"] != post["user_password_confirm"]:
            return self.get(event, path, post, "as senhas devem coincidir", user)
        if not validate_password(post["user_password"]):
            return self.get(event, path, post, "a senha escolhida é muito fraca, forneça uma senha maior", user)

        put_user_password_into_crypto_data_base(user.user_email, post["user_password"])
        return redirect(""), "login", user
