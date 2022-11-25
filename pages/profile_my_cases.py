import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, query_all_user_cases, read_html, translate_size, translate_date, generate_image, sort_dict


class ProfileMyCases(Page):
    def __init__(self):
        Page.__init__(self, "profile_my_cases", html_file="profile_my_cases/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Perfil"})
        user_cases = query_all_user_cases(user.user_email)
        if user_cases:
            user_cases = sort_dict(user_cases, "created_at", True)
            html.esc("html_profile_cases_or_no_cases", list_html_profile_cases(user_cases))
        else:
            html.esc("html_profile_cases_or_no_cases", str(read_html("profile_my_cases/_codes/no_cases")))
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        return self.get(event, path, post, error_msg, user)


def list_html_profile_cases(user_cases):
    full_html = ""
    if user_cases:
        for case in user_cases:
            if case["case_status"] != "deleted":
                html = read_html("profile_my_cases/_codes/profile_cases")
                html.esc("case_photo_val", generate_image(case["case_photo"], "400", "400"))
                html.esc("case_name_val", case["case_name"].title())
                html.esc("case_size_val", translate_size(case["case_size"]).title())
                html.esc("case_date_val", translate_date(case["case_date"]))
                html.esc("case_id_val", case["case_id"])
                if case["case_status"] == "lost":
                    html.esc("case_status_color_val", "lost")
                if case["case_status"] == "found":
                    html.esc("case_status_color_val", "found")
                if case["case_status"] == "was_found":
                    html.esc("case_status_color_val", "returned")
                    html.esc("html_pet_found_message", str(read_html("profile_my_cases/_codes/pet_found_message")))
                if case["case_status"] == "was_lost":
                    html.esc("case_status_color_val", "returned")
                    html.esc("html_pet_found_message", str(read_html("profile_my_cases/_codes/pet_found_message")))
                full_html += str(html)
    return full_html
