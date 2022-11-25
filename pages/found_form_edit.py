import sys
from os import path

from utils.utils import put_entity_into_db

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, redirect, insert_image_form_data, check_image_exists, check_error_msg, validate_date


class FoundFormEdit(Page):
    def __init__(self):
        Page.__init__(self, "found_form_edit", html_file="found_form_edit/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "case" in path:
            return redirect("profile")
        if path["case"]["case_email"] != user.user_email:
            return redirect("profile")

        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Encontrei"})
        check_error_msg(html, error_msg)
        html = insert_image_form_data("case_photo", html)

        if path["case"].get("case_date"):
            html.esc("case_date_val", path["case"]["case_date"])
            html.esc("if_case_date_exists", "focus")
        if path["case"].get("case_age"):
            html.esc("case_age_val", path["case"]["case_age"])
            html.esc("if_case_age_exists", "focus")
        if path["case"].get("case_age_time"):
            html.esc("case_age_time_val", path["case"]["case_age_time"])
            html.esc("if_case_age_time_exists", "focus")
            html.esc("case_age_time_" + path["case"]["case_age_time"].lower() + "_presel", 'selected="selected"')
        if path["case"].get("case_size"):
            html.esc("case_size_val", path["case"]["case_size"])
            html.esc("case_size_" + path["case"]["case_size"].lower() + "_presel", 'selected="selected"')
            html.esc("if_case_size_exists", "focus")
        if path["case"].get("case_description"):
            html.esc("case_description_val", path["case"]["case_description"].strip())
            html.esc("if_case_description_exists", "focus")
        html.esc("case_id_val", path["case"]["case_id"])
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "case" in path:
            return redirect("profile")
        if path["case"]["case_email"] != user.user_email:
            return redirect("profile")

        if not post.get("case_date"):
            return self.get(event, path, post, "é necessário informar a data que você perdeu o seu pet", user)
        if not validate_date(post["case_date"]):
            return self.get(event, path, post, "é necessário informar uma data válida em que você perdeu o seu pet", user)
        if not post.get("case_age"):
            return self.get(event, path, post, "é necessário informar a idade aproximada do seu pet", user)
        if not post.get("case_age_time"):
            return self.get(event, path, post, "é informar se a idade está em anos ou meses", user)
        if not post.get("case_size"):
            return self.get(event, path, post, "é necessário informar o porte do seu pet", user)
        if not post.get("case_photo_image_file"):
            return self.get(event, path, post, "é necessário enviar uma foto do seu pet", user)

        path["case"]["case_date"] = post.get("case_date").lower().strip()
        path["case"]["case_age"] = post.get("case_age").lower().strip()
        path["case"]["case_age_time"] = post.get("case_age_time").lower().strip()
        path["case"]["case_size"] = post.get("case_size").lower().strip()
        path["case"]["case_phone"] = user.user_phone.lower().strip()
        path["case"]["case_description"] = post.get("case_description", "").lower().strip()
        if check_image_exists(post["case_photo_image_file"]):
            path["case"]["case_photo"] = post.get("case_photo_image_file").lower().strip()
        put_entity_into_db(path["case"])
        return redirect("profile_case/" + path["case"]["case_id"])
