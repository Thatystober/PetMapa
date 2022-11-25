import sys
from os import path

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, lambda_constants, parse_html, redirect, generate_qr_code, put_entity_into_db, generate_pdf, invoke_send_case_email, generate_area_cases, generate_suggestion_score, send_emails_to_similar_cases


class FoundMap(Page):
    def __init__(self):
        Page.__init__(self, "found_map", html_file="found_map/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("case"):
            return redirect("found")
        if path["case"]["case_email"] != user.user_email:
            return redirect("found")

        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Encontrei"})
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("case"):
            return redirect("found")
        if path["case"]["case_email"] != user.user_email:
            return redirect("found")

        if post.get("location"):
            path["case"]["case_lat"], path["case"]["case_lon"], path["case"]["case_area"] = format_location(post["location"])
            path["case"]["case_status"] = "found"
            put_entity_into_db(path["case"])
            generate_qr_code(lambda_constants["domain_name_url"] + "/home/" + path["case"]["case_lat"] + "/" + path["case"]["case_lon"], lambda_constants["img_bucket"], path["case"]["case_id"])
            generate_pdf(path["case"]["case_id"])
            area_cases = generate_area_cases(path["case"]["case_lat"], path["case"]["case_lon"], path["case"]["case_type"], path["case"]["case_id"], path["case"]["case_status"])
            if area_cases:
                area_cases = generate_suggestion_score(path["case"], area_cases)
                send_emails_to_similar_cases(area_cases)

            return redirect("found_suggestion/" + path["case_id"])
        return self.get(event, path, post, error_msg, user)


def format_location(location):
    location = location.replace("(", "").replace(")", "").replace(",", "")
    location_lat = location.split(" ")[0]
    location_lon = location.split(" ")[1]
    if location_lat[0] != "-":
        location_lat = "+" + location_lat
    if location_lon[0] != "-":
        location_lon = "+" + location_lon
    location_area = location_lat[:6] + location_lon[:6]
    return location_lat, location_lon, location_area
