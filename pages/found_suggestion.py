import sys
from os import path

from pages.page import check_error_msg, generate_image
from utils.utils import sort_dict

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, redirect, generate_area_cases, read_html, translate_size, translate_age_time


class FoundSuggestion(Page):
    def __init__(self):
        Page.__init__(self, "found_suggestion", html_file="found_suggestion/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("case"):
            return redirect("found")

        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Perdi"})
        html.esc("case_id", path["case_id"])
        area_cases = generate_area_cases(path["case"]["case_lat"], path["case"]["case_lon"], path["case"]["case_type"], path["case"]["case_id"], path["case"]["case_status"])
        if not area_cases:
            return redirect("found_case/" + path["case_id"])
        area_cases = generate_suggestion_score(path["case"], area_cases)
        if area_cases[0]["case_similarity"] < 0.5:
            return redirect("found_case/" + path["case_id"])
        html.esc("html_found_suggestion_cases", list_html_found_suggestion_cases(area_cases))
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("case"):
            return redirect("found")

        return self.get(event, path, post, error_msg, user)


def generate_suggestion_score(current_case, area_cases):
    if area_cases:
        for case in area_cases:
            similarity = 0
            for model in case["case_model"]:
                if model in current_case["case_model"]:
                    similarity += 1
            if case["case_size"] == current_case["case_size"]:
                similarity += 1
            if len(case["case_model"]) > len(current_case["case_model"]):
                case_division = len(case["case_model"]) + 1
            else:
                case_division = len(current_case["case_model"]) + 1
            case["case_similarity"] = similarity / case_division
    area_cases = sort_dict(area_cases, "case_similarity", True)
    return area_cases


def list_html_found_suggestion_cases(area_cases):
    full_html = ""
    if area_cases:
        for case in area_cases:
            html = read_html("lost_suggestion/_codes/lost_suggestion_cases")
            html.esc("case_photo_val", generate_image(case["case_photo"], "180", "180"))
            html.esc("case_name_val", case["case_name"].title())
            html.esc("case_size_val", translate_size(case["case_size"]).title())
            html.esc("case_age_val", case["case_age"])
            html.esc("case_age_time_val", translate_age_time(case["case_age_time"]))
            html.esc("case_lat_val", case["case_lat"])
            html.esc("case_lon_val", case["case_lon"])
            full_html += str(html)
    return full_html
