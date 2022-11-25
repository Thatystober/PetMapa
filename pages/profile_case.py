import sys
from os import path

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, redirect, translate_age_time, translate_size, read_html, put_entity_into_db, translate_date, generate_image


class ProfileCase(Page):
    def __init__(self):
        Page.__init__(self, "profile_case", html_file="profile_case/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "case" in path:
            return redirect("profile")
        if path["case"]["case_email"] != user.user_email:
            return redirect("profile")

        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Perfil"})
        html.esc("case_photo_val", generate_image(path["case"]["case_photo"], "180", "180"))
        html.esc("case_name_val", path["case"]["case_name"].title())
        html.esc("case_date_val", translate_date(path["case"]["case_date"]))
        html.esc("case_size_val", translate_size(path["case"]["case_size"]).title())
        html.esc("case_age_val", path["case"]["case_age"])
        html.esc("case_age_time_val", translate_age_time(path["case"]["case_age_time"]))
        html.esc("case_description_val", path["case"]["case_description"])
        html.esc("case_id_val", path["case"]["case_id"])
        if path["case"]["case_status"] == "found":
            html.esc("html_delete_case", show_html_delete_case(path["url"]))
            html.esc("html_case_edit", show_html_case_edit(path["case"], path["url"]))
            html.esc("html_lost_found_button_or_returned_message", show_html_lost_found_button(path["case"], path["url"]))
            html.esc("html_check_on_the_map", show_html_check_on_the_map(path["case"]))
        if path["case"]["case_status"] == "lost":
            html.esc("html_delete_case", show_html_delete_case(path["url"]))
            html.esc("html_case_edit", show_html_case_edit(path["case"], path["url"]))
            html.esc("html_lost_found_button_or_returned_message", show_html_lost_found_button(path["case"], path["url"]))
            html.esc("html_check_on_the_map", show_html_check_on_the_map(path["case"]))
        if path["case"]["case_status"] == "was_lost" or path["case"]["case_status"] == "was_found":
            html.esc("html_lost_found_button_or_returned_message", show_html_returned_button())

        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not "case" in path:
            return redirect("profile")
        if path["case"]["case_email"] != user.user_email:
            return redirect("profile")

        if post.get("was_lost"):
            path["case"]["case_status"] = "was_lost"
            path["case"]["case_area"] = "+00.00+00.00"
            put_entity_into_db(path["case"])
            return redirect("profile_my_cases")
        if post.get("was_found"):
            path["case"]["case_status"] = "was_found"
            path["case"]["case_area"] = "+00.00+00.00"
            put_entity_into_db(path["case"])
            return redirect("profile_my_cases")
        if post.get("delete"):
            path["case"]["case_status"] = "deleted"
            path["case"]["case_area"] = "+00.00+00.00"
            put_entity_into_db(path["case"])
            return redirect("profile_my_cases")
        return self.get(event, path, post, error_msg, user)


def show_html_returned_button():
    return str(read_html("profile_case/_codes/returned_button"))


def show_html_delete_case(user_url):
    html = read_html("profile_case/_codes/delete_case")
    html.esc("user_url_val", user_url)
    return str(html)


def show_html_lost_found_button(case, user_url):
    full_html = ""
    if case:
        html = read_html("profile_case/_codes/lost_found_button")
        html.esc("user_url_val", user_url)
        if case["case_status"] == "found":
            html.esc("found_or_lost_message_val", "Encontrei o Dono!")
            html.esc("was_lost_or_found_val", "was_found")
        if case["case_status"] == "lost":
            html.esc("found_or_lost_message_val", "Encontrei o Pet!")
            html.esc("was_lost_or_found_val", "was_lost")
        full_html += str(html)
    return full_html


def show_html_check_on_the_map(case):
    full_html = ""
    if case:
        html = read_html("profile_case/_codes/check_on_the_map")
        html.esc("case_lat_val", case["case_lat"])
        html.esc("case_lon_val", case["case_lon"])
        full_html += str(html)
    return full_html


def show_html_case_edit(case, user_url):
    full_html = ""
    if case:
        html = read_html("profile_case/_codes/case_edit")
        html.esc("user_url_val", user_url)
        html.esc("case_lost_or_found_val", case["case_status"])
        html.esc("case_id_val", case["case_id"])
        full_html += str(html)
    return full_html
