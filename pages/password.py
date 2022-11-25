import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, User, lambda_constants, ses_client, parse_html, redirect, check_error_msg, read_html


class Password(Page):
    def __init__(self):
        Page.__init__(self, "password", html_file="password/index", bypass=True, public=True)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "user_email" in path:
            return redirect("login")
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Senha"})
        check_error_msg(html, error_msg)
        html.esc("user_email_val", path["user_email"])
        if post.get("user_password"):
            html.esc("user_password_val", post["user_password"])
            html.esc("if_user_password_exists", "focus")
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "user_email" in path:
            return redirect("login")
        if not "user_password" in post and not "user_email_forgot" in post:
            return self.get(event, path, post, "Verifique o campo: " + "Senha", user)
        if "user_password" in post:
            user = User(user_email=path["user_email"])
            user.load_information(data_base=True)
            if user.user_password != post["user_password"]:
                return self.get(event, path, post, "Senha incorreta", user)
            user.update_auth_token()
            return "Login completed", "login", user
        elif "user_email_forgot" in post:
            user = User(user_email=post["user_email_forgot"])
            user.load_information()
            if user.user_valid:
                user.update_email_token()
                if send_email_password(user):
                    ### REDIRECT TO PASSWORD SENT
                    return redirect("password_email_sent/" + path["user_email_encoded"])
                else:
                    return self.get(event, path, post, "Não foi possível enviar o email de reset de senha, entre em contato com o suporte", user)
        return self.get(event, path, post, "Digite sua senha", user)


def send_email_password(user):
    html = read_html("password_email_sent/codes/email")
    html.esc("user_name_val", user.user_name.title())
    html.esc("user_email_token_val", user.user_email_token)
    title = "Redefinição de senha em Petmapa"
    try:
        result = ses_client.send_email(
            Destination={"ToAddresses": [user.user_email]},
            Message={
                "Body": {
                    "Html": {
                        "Charset": "utf-8",
                        "Data": str(html),
                    },
                    "Text": {
                        "Charset": "utf-8",
                        "Data": str(html),
                    },
                },
                "Subject": {
                    "Charset": "utf-8",
                    "Data": title,
                },
            },
            Source="suporte@petmapa.com.br",
            ConfigurationSetName=lambda_constants["domain_name"],
        )
        return True
    except:
        return False
