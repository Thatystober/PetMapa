from utils.utils import put_entity_into_db
from time import time
from uuid import uuid4


class Case:
    pk = ""
    sk = ""
    case_email = ""
    case_id = ""
    case_status = ""
    case_model = []
    case_name = ""
    case_date = ""
    case_age = ""
    case_age_time = ""
    case_size = ""
    case_description = ""
    case_photo = ""
    case_phone = ""
    case_lat = "+00.00"
    case_lon = "+00.00"
    case_area = "+00.00+00.00"
    created_at = str(int(time()))
    entity = "case"

    def __init__(self, case_email="", case_status="", case_id=str(uuid4())) -> None:
        self.pk = "user#" + case_email
        self.sk = "case#" + case_id
        self.case_email = case_email
        self.case_id = case_id
        self.case_status = case_status
        self.case_model = []
        self.case_name = ""
        self.case_date = ""
        self.case_age = ""
        self.case_age_time = ""
        self.case_size = ""
        self.case_description = ""
        self.case_photo = ""
        self.case_phone = ""
        self.case_lat = "+00.00"
        self.case_lon = "+00.00"
        self.case_area = "+00.00+00.00"
        self.created_at = str(int(time()))
        self.entity = "case"

    def create_case(self, post):
        for param in post:
            setattr(self, param, post[param])
        put_entity_into_db(self.__dict__)
