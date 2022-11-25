import sys
from os import path
from uuid import uuid4

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, Case, parse_html, redirect, insert_image_form_data, check_image_exists, check_error_msg, validate_date


class FoundForm(Page):
    def __init__(self):
        Page.__init__(self, "found_form", html_file="found_form/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("case_type"):
            return redirect("found")
        if not path.get("case_model"):
            return redirect("found_model/" + path["case_type"])

        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Encontrei"})
        check_error_msg(html, error_msg)
        html.esc("case_type_val", path["case_type"])
        html = insert_image_form_data("case_photo", html)
        if post.get("case_date"):
            html.esc("case_date_val", post["case_date"])
            html.esc("if_case_date_exists", "focus")
        if post.get("case_age"):
            html.esc("case_age_val", post["case_age"])
            html.esc("if_case_age_exists", "focus")
        if post.get("case_age_time"):
            html.esc("case_age_time_val", post["case_age_time"])
            html.esc("if_case_age_time_exists", "focus")
            html.esc("case_age_time_" + post["case_age_time"].lower() + "_presel", 'selected="selected"')
        if post.get("case_size"):
            html.esc("case_size_val", post["case_size"])
            html.esc("case_size_" + post["case_size"].lower() + "_presel", 'selected="selected"')
            html.esc("if_case_size_exists", "focus")
        if post.get("case_description"):
            html.esc("case_description_val", post["case_description"].strip())
            html.esc("if_case_description_exists", "focus")
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("case_type"):
            return redirect("found")
        if not path.get("case_model"):
            return redirect("found_model/" + path["case_type"])

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
        if not check_image_exists(post["case_photo_image_file"]):
            return self.get(event, path, post, "é necessário enviar uma foto do seu pet", user)
        post["case_phone"] = user.user_phone
        post = format_case_data_params(path, post)

        new_case = Case(case_email=user.user_email, case_status="pending", case_id=str(uuid4()))
        new_case.create_case(post)

        return redirect("found_map/" + new_case.case_id)


def format_case_data_params(path, post):
    filtered_post = {}
    filtered_post["case_type"] = path.get("case_type").lower().strip()
    filtered_post["case_model"] = path.get("case_model").lower().strip().split("-")
    filtered_post["case_date"] = post.get("case_date").lower().strip()
    filtered_post["case_age"] = post.get("case_age").lower().strip()
    filtered_post["case_age_time"] = post.get("case_age_time").lower().strip()
    filtered_post["case_size"] = post.get("case_size").lower().strip()
    filtered_post["case_phone"] = post.get("case_phone").lower().strip()
    filtered_post["case_description"] = post.get("case_description", "").lower().strip()
    filtered_post["case_photo"] = post.get("case_photo_image_file").lower().strip()
    return filtered_post
