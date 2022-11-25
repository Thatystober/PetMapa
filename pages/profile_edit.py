import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, format_to_mobile_phone_number, refresh_response_cache, check_error_msg, query_all_user_cases, validate_br_phone, put_entity_into_db, update_case_phone


class ProfileEdit(Page):
    def __init__(self):
        Page.__init__(self, "profile_edit", html_file="profile_edit/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Perfil"})
        check_error_msg(html, error_msg)
        html.esc("user_name_val", user.user_name.title())
        html.esc("user_email_val", user.user_email)
        html.esc("user_last_name_val", user.user_last_name.title())
        html.esc("user_phone_val", format_to_mobile_phone_number(user.user_phone))
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not post.get("user_name"):
            return self.get(event, path, post, "verifique o campo nome", user)
        if not post.get("user_last_name"):
            return self.get(event, path, post, "verifique o campo sobrenome", user)
        if not post.get("user_phone"):
            return self.get(event, path, post, "verifique o campo telefone", user)
        if not validate_br_phone(post["user_phone"]):
            return self.get(event, path, post, "o número de telefone fornecido é inválido", user)
        post["user_phone"] = post["user_phone"].lower().strip().replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        if user.user_phone != post["user_phone"]:
            update_all_user_cases_phone(user.user_email, post["user_phone"])
        user.user_name = post["user_name"].lower().strip()
        user.user_last_name = post["user_last_name"].lower().strip()
        user.user_phone = post["user_phone"].lower().strip()
        put_entity_into_db(user.__dict__)
        return self.get(event, path, post, "dados atualizados com sucesso", user)


def update_all_user_cases_phone(user_email, user_new_phone):
    all_user_cases = query_all_user_cases(user_email)
    if all_user_cases:
        for case in all_user_cases:
            case["case_phone"] = user_new_phone
            update_case_phone(case)
    return
