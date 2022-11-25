from utils.utils import (
    EncryptedTable,
    lambda_constants,
    aws_kms_cmp,
    actions,
    table,
    clear_caches,
    put_entity_into_db,
    update_user_to_cache,
    get_user_from_cache,
    get_user_auth_token_from_cache,
    get_user_auth_token_from_db,
    put_user_email_token_into_db,
    put_user_auth_token_into_db,
    put_entity_into_db,
    execute_get_item,
)
from time import time
from uuid import uuid4
from urllib.parse import parse_qs


class User:
    pk = ""
    sk = ""
    user_email = ""
    user_password = ""
    user_name = ""
    user_last_name = ""
    user_phone = ""
    user_is_admin = False
    user_valid = False
    created_at = str(int(time()))
    entity = "user"

    def __init__(self, user_email="") -> None:
        self.pk = "user#" + user_email
        self.sk = "user#" + user_email
        self.user_email = user_email
        self.user_password = ""
        self.user_name = ""
        self.user_last_name = ""
        self.user_phone = ""
        self.user_is_admin = False
        self.user_valid = False
        self.created_at = str(int(time()))
        self.entity = "user"

    def update_auth_token(self):
        self.user_auth_token = str(uuid4())
        put_user_auth_token_into_db(self.user_auth_token, self.user_email)

    def update_email_token(self):
        self.user_email_token = str(uuid4())
        put_user_email_token_into_db(self.user_email_token, self.user_email)

    def create_user(self, post):
        for p in post:
            setattr(self, p, post[p])
        self.update_auth_token()
        put_user_password_into_crypto_data_base(self.user_email, self.user_password)
        del self.user_password
        put_entity_into_db(self.__dict__)
        clear_caches()

    def get_user_with_auth_token(self, user_auth_token):
        if not user_auth_token:
            return None
        user_email_found = get_user_auth_token_from_cache(user_auth_token)
        if user_email_found is None:
            user_email_found = get_user_auth_token_from_db(user_auth_token)
            if user_email_found:
                if "auth_user_email" in user_email_found:
                    user_email_found = user_email_found["auth_user_email"]
        if user_email_found:
            self.user_email = user_email_found
            self.load_information()
            return
        self.valid = False
        print("ERROR: User not found with user_auth_token " + str(user_auth_token))

    def load_information(self, data_base=False):
        if self.user_email == "":
            return
        if not data_base:
            user_found = get_user_from_cache(self.user_email)
            if user_found is None:
                user_found = get_user_from_db(self.user_email)
        else:
            user_found = get_user_from_db(self.user_email)
        if user_found:
            for attribute in user_found:
                setattr(self, attribute, user_found[attribute])
            if data_base:
                self.user_password = get_user_password_into_crypto_data_base(self.user_email)
                return
            update_user_to_cache(self.user_email, self.__dict__)
        return

    def update_user(self, post={}):
        if self.user_valid == False:
            return
        if post:
            for p in post:
                setattr(self, p, post[p])
        if self.user_password != "":
            put_user_password_into_crypto_data_base(self.user_email, self.user_password)
            del self.user_password
        put_entity_into_db(self.__dict__)
        clear_caches()


def get_user_from_db(user_email):
    input = {"TableName": lambda_constants["table"], "Key": {"pk": {"S": "user#" + str(user_email)}, "sk": {"S": "user#" + str(user_email)}}}
    return execute_get_item(input)


def put_user_password_into_crypto_data_base(user_email, user_pass):
    encrypted_table = EncryptedTable(table=table, materials_provider=aws_kms_cmp, attribute_actions=actions)
    password_item = {"pk": "user#" + str(user_email), "sk": "pass#" + str(user_email), "user_password": str(user_pass)}
    return encrypted_table.put_item(Item=password_item)


def get_user_password_into_crypto_data_base(user_email):
    encrypted_table = EncryptedTable(table=table, materials_provider=aws_kms_cmp, attribute_actions=actions)
    password_item = {"pk": "user#" + str(user_email), "sk": "pass#" + str(user_email)}
    user_password = encrypted_table.get_item(Key=password_item)
    if "Item" in user_password:
        if "user_password" in user_password["Item"]:
            return user_password["Item"]["user_password"]
    return None


def get_user_from_event(event):
    if "cookies" in event:
        for cookie in event["cookies"]:
            if "__Secure-token" in cookie:
                if parse_qs(cookie):  # make sure it has auth_token after secure-token
                    cookies = parse_qs(cookie)["__Secure-token"][0]
                    user = User()
                    user.get_user_with_auth_token(cookies)
                    if user.user_valid:
                        return user
    if "pathParameters" in event:
        if "user_email_token" in event["pathParameters"]:
            user = User()
            user.get_user_with_auth_token(event["pathParameters"]["user_email_token"])
            if user.user_valid:
                return user
    return None
