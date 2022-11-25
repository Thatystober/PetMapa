import sys
from os import path

sys.path.append(path.join(path.dirname(__file__)))

from pages.home import Home
from pages.login import Login
from pages.password import Password
from pages.register import Register
from pages.exit import Exit
from pages.password_reset import PasswordReset
from pages.password_email_sent import PasswordEmailSent
from pages.register_password import RegisterPassword
from pages.donation import Donation
from pages.profile import Profile
from pages.profile_edit import ProfileEdit
from pages.profile_password import ProfilePassword
from pages.profile_my_cases import ProfileMyCases
from pages.profile_case import ProfileCase
from pages.found import Found
from pages.found_model import FoundModel
from pages.found_form import FoundForm
from pages.found_map import FoundMap
from pages.found_suggestion import FoundSuggestion
from pages.found_case import FoundCase
from pages.found_form_edit import FoundFormEdit
from pages.lost import Lost
from pages.lost_model import LostModel
from pages.lost_form import LostForm
from pages.lost_form_edit import LostFormEdit
from pages.lost_map import LostMap
from pages.lost_suggestion import LostSuggestion
from pages.lost_case import LostCase
from pages.case import Case
from pages.not_found import NotFound


class PageManager:
    pages_get = {}
    pages_post = {}

    def __init__(self) -> None:
        self.pages = [LostFormEdit(), ProfileMyCases(), ProfilePassword(), LostSuggestion(), Lost(), Found(), FoundCase(), FoundFormEdit(), FoundMap(), FoundSuggestion(), FoundModel(), FoundForm(), Profile(), ProfileEdit(), ProfileCase(), Donation(), PasswordReset(), Exit(), Password(), PasswordEmailSent(), Register(), RegisterPassword(), Login(), Home(), LostModel(), LostForm(), LostMap(), LostCase(), Case(), NotFound()]
        self.pages_get = {}
        self.pages_post = {}
        for page in self.pages:
            if callable(getattr(page, "get", None)):
                self.pages_get[page.route] = page
            if callable(getattr(page, "post", None)):
                self.pages_post[page.route] = page

    def open_page(self, page):
        self.pages_get[page]
