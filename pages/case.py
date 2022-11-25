import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, lambda_constants, parse_html, redirect, format_to_mobile_phone_number, translate_size, translate_date, redirect, translate_age_time, generate_image


class Case(Page):
    def __init__(self):
        Page.__init__(self, "case", html_file="case/index", bypass=False, public=True)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("case"):
            return redirect("lost")

        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Perdi"})
        if path["case"]["case_status"] == "lost":
            html.esc("search_val", "PROCURA-SE")
        elif path["case"]["case_status"] == "found":
            html.esc("search_val", "PROCURO MEU DONO(A)")
        html.esc("case_photo_val", generate_image(path["case"]["case_photo"], "450", "400"))
        html.esc("case_name_val", path["case"]["case_name"].title())
        html.esc("case_size_val", translate_size(path["case"]["case_size"]).title())
        html.esc("case_age_val", path["case"]["case_age"])
        html.esc("case_age_time_val", translate_age_time(path["case"]["case_age_time"]))
        html.esc("case_phone_val", format_to_mobile_phone_number(path["case"]["case_phone"]))
        html.esc("case_date_val", translate_date(path["case"]["case_date"]))
        html.esc("case_description_val", path["case"]["case_description"])
        html.esc("case_id_val", path["case"]["case_id"])
        html.esc("case_lat_val", path["case"]["case_lat"])
        html.esc("case_lon_val", path["case"]["case_lon"])
        html.esc("google_api_key_val", lambda_constants["google_api_key"])
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        return self.get(event, path, post, error_msg, user)
