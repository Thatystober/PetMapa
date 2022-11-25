import sys
from os import path
from random import choice

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, lambda_constants, parse_html, read_html, query_all_cases, generate_image, translate_date


class Home(Page):
    def __init__(self):
        Page.__init__(self, "home", html_file="home/index", bypass=False, public=True)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Home"})
        if user:
            html.esc("html_login_or_logout_button", str(read_html("home/_codes/html_logout_button")))
        else:
            html.esc("html_login_or_logout_button", str(read_html("home/_codes/html_login_button")))
        html.esc("google_api_key_val", lambda_constants["google_api_key"])
        cases = query_all_cases()
        html.esc("html_initialize_map", show_html_initialize_map(path, cases))
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        return self.get(event, path, post, error_msg, user)


def show_html_initialize_map(path, cases):
    html = read_html("home/_codes/initialize_map")
    if path.get("case_lat") and path.get("case_lon"):
        html.esc("browser_or_path_lat_val", path["case_lat"])
        html.esc("browser_or_path_lon_val", path["case_lon"])
    else:
        html.esc("browser_or_path_lat_val", "position.coords.latitude")
        html.esc("browser_or_path_lon_val", "position.coords.longitude")
    html.esc("html_home_cases", list_html_home_cases(cases))
    return str(html)


def list_html_home_cases(cases):
    full_html = ""
    if cases:
        for index, case in enumerate(cases):
            if case["case_status"] == "lost" or case["case_status"] == "found":
                html = read_html("home/_codes/home_cases")
                html.esc("index_val", str(index + 1))
                html.esc("case_lat_val", case["case_lat"])
                html.esc("case_lon_val", case["case_lon"])
                html.esc("case_name_val", case["case_name"].title())
                html.esc("case_description_val", case["case_description"])
                html.esc("case_date_val", translate_date(case["case_date"]))
                html.esc("case_photo_val", generate_image(case["case_photo"], "180", "180"))
                html.esc("case_icon_val", generate_home_icon(case))
                html.esc("case_phone_val", case["case_phone"])
                if case['case_status'] == 'found':
                    html.esc("case_status_val", "Encontrado")
                elif case['case_status'] == 'lost':
                    html.esc("case_status_val", "Perdido")
                full_html += str(html)
    return full_html


def generate_home_icon(case):
    return case["case_type"] + "_" + case["case_status"] + "_" + (case["case_model"][0]) + ".png"
