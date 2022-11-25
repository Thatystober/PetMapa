import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, get_user_password_into_crypto_data_base, check_error_msg, get_user_password_into_crypto_data_base, put_user_password_into_crypto_data_base, validate_password


class ProfilePassword(Page):
    def __init__(self):
        Page.__init__(self, "profile_password", html_file="profile_password/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Perfil"})
        check_error_msg(html, error_msg)
        if post.get("user_old_password"):
            html.esc("if_user_old_password", "focus")
            html.esc("user_old_password_val", post["user_old_password"])
        if post.get("user_new_password"):
            html.esc("if_user_new_password", "focus")
            html.esc("user_new_password_val", post["user_new_password"])
        if post.get("user_new_password_confirm"):
            html.esc("if_user_new_password_confirm", "focus")
            html.esc("user_new_password_confirm_val", post["user_new_password_confirm"])
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not post.get("user_old_password"):
            return self.get(event, path, post, "é necessário informar a senha atual", user)
        if not post.get("user_new_password"):
            return self.get(event, path, post, "é necessário informar a nova senha que você deseja utilizar", user)
        if not post.get("user_new_password_confirm"):
            return self.get(event, path, post, "é necessário confirmar a nova senha", user)
        if not validate_password(post["user_new_password"]):
            return self.get(event, path, post, "a senha escolhida é muito fraca, forneça uma senha maior", user)
        user_actual_password = get_user_password_into_crypto_data_base(user.user_email)
        if post.get("user_old_password") != user_actual_password:
            return self.get(event, path, post, "a senha atual fornecida está incorreta", user)
        if post["user_new_password"] != post["user_new_password_confirm"]:
            return self.get(event, path, post, "a nova senha e a confirmação de senha devem coincidir", user)
        put_user_password_into_crypto_data_base(user.user_email, post["user_new_password"])
        return self.get(event, path, post, "dados atualizados com sucesso", user)
