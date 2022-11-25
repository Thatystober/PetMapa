import sys
from os import path


sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, format_to_mobile_phone_number, translate_size, translate_date, redirect, generate_image, translate_age_time


class LostCase(Page):
    def __init__(self):
        Page.__init__(self, "lost_case", html_file="lost_case/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("case"):
            return redirect("lost")
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Perdi"})
        html.esc("case_photo_val", generate_image(path["case"]["case_photo"], "180", "180"))
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
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        return self.get(event, path, post, error_msg, user)
