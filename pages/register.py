import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, User, parse_html, redirect, check_error_msg, validate_email, validate_br_phone


class Register(Page):
    def __init__(self):
        Page.__init__(self, "register", html_file="register/index", bypass=True, public=True)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "user_email" in path:
            return redirect("register_password")
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Cadastro"})
        html.esc("user_email_val", path["user_email"])
        html.esc("if_user_email_exists", "focus")
        check_error_msg(html, error_msg)
        if post.get("user_name"):
            html.esc("user_name_val", post["user_name"].title())
            html.esc("if_user_name_exists", "focus")
        if post.get("user_last_name"):
            html.esc("user_last_name_val", post["user_last_name"].title())
            html.esc("if_user_last_name_exists", "focus")
        if post.get("user_phone"):
            html.esc("user_phone_val", post["user_phone"])
            html.esc("if_user_phone_exists", "focus")
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "user_email" in path:
            return redirect("login")
        if not post.get("user_email"):
            return self.get(event, path, post, "verifique o campo email", user)
        if not post.get("user_name"):
            return self.get(event, path, post, "verifique o campo nome", user)
        if not post.get("user_last_name"):
            return self.get(event, path, post, "verifique o campo sobrenome", user)
        if not post.get("user_phone"):
            return self.get(event, path, post, "verifique o campo telefone", user)
        if not validate_br_phone(post["user_phone"]):
            return self.get(event, path, post, "o número de telefone fornecido é inválido", user)
        if not validate_email(post["user_email"][:45]):
            return self.get(event, path, post, "verifique o email fornecido", user)
        post = format_register_parameters(post)
        user = User(user_email=post["user_email"])
        user.create_user(post)
        return redirect("register_password/" + path["user_email_encoded"])


def format_register_parameters(post):
    filtered_post = {}
    filtered_post["user_email"] = post.get("user_email", "").lower().strip()
    filtered_post["user_name"] = (post.get("user_name", "")).lower().strip()
    filtered_post["user_last_name"] = (post.get("user_last_name", "")).lower().strip()
    filtered_post["user_phone"] = (post.get("user_phone", "")).lower().strip().replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
    return filtered_post
