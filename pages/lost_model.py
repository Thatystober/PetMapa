import sys
from os import path

from pages.page import check_error_msg

sys.path.append(path.join(path.dirname(__file__)))
from page import Page, parse_html, redirect


class LostModel(Page):
    def __init__(self):
        Page.__init__(self, "lost_model", html_file="lost_model/index", bypass=False, public=False)

    def get(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("case_type"):
            return redirect("lost")
        html = parse_html(self.html_file, self.route, path, event, user, {"page_title_val": "Perdi"})
        check_error_msg(html, error_msg)
        html.esc("case_type_val", path["case_type"])
        return str(html)

    def post(self, event=None, path=None, post={}, error_msg=None, user=None):
        if not path.get("case_type"):
            return redirect("lost")
        case_model = ""
        for param in post:
            if "case_model" in param:
                case_model += post[param] + "-"
        if case_model:
            return redirect("lost_form/" + path["case_type"] + "/" + case_model[:-1])
        return self.get(event, path, post, "selecione imagens semelhantes ao seu pet", user)
