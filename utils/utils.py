from os import path
from re import findall, sub, search, escape, compile, finditer
from boto3 import client, resource
from botocore.client import Config
from json import dumps, load, loads
from base64 import b64encode, b64decode
from datetime import datetime
from copy import deepcopy
import dateutil.parser as dp
from itertools import cycle
from phonenumbers import parse as phone_parse, is_valid_number
from time import time
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from dynamodb_encryption_sdk.encrypted.table import EncryptedTable
from dynamodb_encryption_sdk.identifiers import CryptoAction
from dynamodb_encryption_sdk.material_providers.aws_kms import AwsKmsCryptographicMaterialsProvider
from dynamodb_encryption_sdk.structures import AttributeActions

domain_name = "petmapa"
lambda_constants = {
    "domain_name": domain_name,
    "domain_name_url": "https://encontre." + domain_name + ".com.br",
    "table": domain_name,
    "region": "sa-east-1",
    "cdn_bucket": "cdn." + domain_name + ".com.br",
    "cdn": "https://cdn." + domain_name + ".com.br",
    "img_bucket": "img." + domain_name + ".com.br",
    "img_cdn": "https://img." + domain_name + ".com.br",
    "file_cdn": "https://s3.sa-east-1.amazonaws.com/img." + domain_name + ".com.br",
    "google_api_key": "AIzaSyArXlxslmh0G1IIofKC4Tz1Pi_QR9K3aRY",
    # "video_bucket": "video." + domain_name + ".com.br",
    # "video_cdn": "https://video." + domain_name + ".com.br",
}
s3 = resource("s3")
lambda_client = client("lambda", lambda_constants["region"])
sqs_client = client("sqs", region_name=lambda_constants["region"])
s3_client = client("s3", lambda_constants["region"], config=Config(s3={"addressing_style": "path"}))
temp_s3_client = client("s3", lambda_constants["region"], aws_access_key_id="AKIAU3RZLIN7SGHMR3MI", aws_secret_access_key="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")
ses_client = client("ses", region_name=lambda_constants["region"])
sesv2_client = client("sesv2", region_name=lambda_constants["region"])
table = resource("dynamodb").Table(lambda_constants["table"])
dynamodb_client = client("dynamodb", region_name="sa-east-1")
actions = AttributeActions(default_action=CryptoAction.ENCRYPT_AND_SIGN)
aws_kms_cmp = AwsKmsCryptographicMaterialsProvider(key_id="2b3e0412-4d41-44f1-ac16-f5151a9c9dad")
encrypted_table = EncryptedTable(table=table, materials_provider=aws_kms_cmp, attribute_actions=actions)
last_post_event = ""


def check_image_exists(image_name):
    try:
        s3_client.head_object(Bucket=lambda_constants["img_bucket"], Key=str(image_name))
        return True
    except:
        return False


### GET FROM EVENT ###


def get_first_param_in_raw_path(event):
    if "rawPath" in event:
        route = event["rawPath"].split("/")[1]
        return route
    return None


def check_if_mobile_from_event(event):
    try:
        if "windows" in event["headers"]["user-agent"].lower():
            return False
        if "mac" in event["headers"]["user-agent"].lower():
            return False
        return True
    except:
        return False


def get_headers_from_event(event):
    if "headers" in event:
        return event["headers"]
    return None


def get_user_ip_from_event(event):
    if "headers" in event:
        if "x-forwarded-for" in event["headers"]:
            return event["headers"]["x-forwarded-for"]
        return None
    return None


def get_user_ua_mobile_from_event(event):
    if "headers" in event:
        if "sec-ch-ua-mobile" in event["headers"]:
            return event["headers"]["sec-ch-ua-mobile"]
        return None
    return None


def get_user_ua_platform_from_event(event):
    if "headers" in event:
        if "sec-ch-ua-platform" in event["headers"]:
            return event["headers"]["sec-ch-ua-platform"]
        return None
    return None


def get_user_agent_from_event(event):
    if "headers" in event:
        if "user-agent" in event["headers"]:
            return event["headers"]["user-agent"]
        return None
    return None


def get_domain_name_from_event(event):
    try:
        return event["requestContext"]["domainName"]
    except:
        return ""


def get_method_from_event(event):
    try:
        return event["requestContext"]["http"]["method"]
    except:
        return ""


def get_path_from_event(event):
    if "pathParameters" in event:
        return event["pathParameters"]
    return {}


def get_url_from_event(event):
    if not event:
        return ""
    if "requestContext" in event:
        if "http" in event["requestContext"]:
            if "path" in event["requestContext"]["http"]:
                return str(event["requestContext"]["http"]["path"])[1:]
    return ""


### DECODE / FORMAT / VALIDATE ###


def camel_case_split(identifier):
    matches = finditer(".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)", identifier)
    return [m.group(0) for m in matches]


def get_class_filename(object_name):
    separator = "_"
    array_strings = camel_case_split(object_name)
    return separator.join(array_strings).lower()


def encode_to_b64(string):
    sample_string_bytes = str(string).encode("ascii")
    base64_bytes = b64encode(sample_string_bytes)
    base64_string = base64_bytes.decode("ascii")
    return base64_string


def decode_from_b64(string):
    base64_bytes = str(string).encode("ascii")
    try:
        sample_string_bytes = b64decode(base64_bytes)
        sample_string = sample_string_bytes.decode("ascii")
        return sample_string
    except:
        return None


def format_to_postal_code(postal_code):
    return "{}.{}-{}".format(postal_code[:2], postal_code[2:5], postal_code[5:])


def format_to_mobile_phone_number(mobile_phone_number):
    return "({}) {}-{}".format(mobile_phone_number[:2], mobile_phone_number[2:7], mobile_phone_number[7:])


def format_to_cpf(mobile_phone_number):
    return "{}.{}.{}-{}".format(mobile_phone_number[:3], mobile_phone_number[3:6], mobile_phone_number[6:9], mobile_phone_number[9:11])


def format_to_cnpj(user_cnpj):
    return "{}.{}.{}/{}-{}".format(user_cnpj[:2], user_cnpj[2:5], user_cnpj[5:8], user_cnpj[8:12], user_cnpj[12:])


def format_to_brl_money(money):
    money = str(money).replace(".", "").replace(",", "")
    if len(money) < 6:
        return "{},{}".format(money[:-2], money[-2:])
    else:
        return "{}.{},{}".format(money[:-5], money[-5:-2], money[-2:])


def format_to_usd_money(money):
    return format_to_brl_money(money).replace(",", ".")


def format_to_ddd(ddd_number):
    return "({})".format(ddd_number[:2])


def format_to_phone_number_without_ddd(phone_number):
    return "{}-{}".format(phone_number[:4], phone_number[4:])


def format_total_time_to_hh_mm_ss(time):
    time = str(round((time.real * 10) * (6)))
    while len(time) < 6:
        time = "0" + time
    return "{}:{}:{}".format(time[:2], time[2:4], time[4:6])


def format_html_time_to_unixtime(html_time):
    parsed_t = dp.parse(html_time)
    t_in_seconds = parsed_t.timestamp()
    return str(round(int(t_in_seconds)))


def format_unixtime_to_htmltime(unix_time):
    return datetime.fromtimestamp(int(float(unix_time))).strftime("%d/%m/%YT%H:%M")


def format_unixtime_to_datetime(unix_time):
    return datetime.fromtimestamp(int(float(unix_time))).strftime("%d/%m/%Y-%H:%M")


def format_unixtime_to_date(unix_time):
    return datetime.fromtimestamp(int(float(unix_time))).strftime("%d/%m/%Y")


def format_unixtime_to_HM_time(unix_time):
    return datetime.fromtimestamp(int(float(unix_time))).strftime("%H:%M")


def format_unixtime_to_HMS_time(unix_time):
    return datetime.fromtimestamp(int(float(unix_time))).strftime("%H:%M:%S")


def format_event_address(event_address):
    return str(event_address.split("__")[0]), str(event_address.split("__")[1].replace("_", "#"))


def format_to_letters_only(string):
    return sub(r"[^a-zA-Z]", "", string)


def format_to_letters_and_spaces(string):
    return sub(r"[^a-zA-Z\s]", "", string)


def format_to_numbers_only(string):
    return sub(r"[^0-9]", "", string)


def format_to_one_name(string):
    string = string[:45].strip().split(" ")[0]
    return sub(r"[^a-zA-Z]", "", string)


def format_to_names(string):
    string = string[:45].strip()
    strings = string.split(" ")
    new_string = ""
    for string in strings:
        new_string += " " + sub(r"[^a-zA-Z]", "", string)
    if new_string == "" or new_string == " ":
        return "not informed"
    return new_string.strip()


def check_image_exists(image_name):
    try:
        s3_client.head_object(Bucket=lambda_constants["img_bucket"], Key=str(image_name))
        return True
    except:
        return False


def check_if_number(number):
    try:
        price = int(price)
        return True
    except:
        return False


def check_if_money(money):
    try:
        money = money.replace(".", "").replace(",", "")
        money = int(money)
        return True
    except:
        return False


def validate_date(date):
    try:
        dateObject = datetime.strptime(date, "%Y-%m-%d")
        return True
    except:
        return False


def validate_email(email):
    regex_email = "([A-Za-z0-9]+[._])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
    if (search(regex_email, email)) is None:
        return False
    else:
        return True


def validate_password(password):
    try:
        if len(str(password)) < 4:
            return False
        password = password[:45].strip()
        return True
    except:
        return False


def validate_field(field):
    if (field == None) or (field == "") or (field == " ") or (field.strip() == " ") or (field.strip() == "") or (len(field) > 500):
        return False
    return True


def validate_htmltime(html_time):
    try:
        parsed_t = dp.parse(html_time)
        t_in_seconds = parsed_t.timestamp()
        datetime.fromtimestamp(int(float(t_in_seconds))).strftime("%d/%m/%Y-%H:%M")
        return True
    except:
        print("ERROR - Cannot validate htmltime")
        return False


def validate_legal_id(cpf):
    numbers = [int(digit) for digit in cpf if digit.isdigit()]
    if len(numbers) != 11 or len(set(numbers)) == 1:
        return False
    sum_of_products = sum(a * b for a, b in zip(numbers[0:9], range(10, 1, -1)))
    expected_digit = (sum_of_products * 10 % 11) % 10
    if numbers[9] != expected_digit:
        return False
    sum_of_products = sum(a * b for a, b in zip(numbers[0:10], range(11, 1, -1)))
    expected_digit = (sum_of_products * 10 % 11) % 10
    if numbers[10] != expected_digit:
        return False
    return True


def validate_legal_cnpj(cnpj, lenght_cnpj=14):
    if len(cnpj) != lenght_cnpj:
        return False
    if cnpj in (c * lenght_cnpj for c in "1234567890"):
        return False
    cnpj_r = cnpj[::-1]
    for i in range(2, 0, -1):
        cnpj_enum = zip(cycle(range(2, 10)), cnpj_r[i:])
        dv = sum(map(lambda x: int(x[1]) * x[0], cnpj_enum)) * 10 % 11
        if cnpj_r[i - 1 : i] != str(dv % 10):
            return False
    return True


def validate_br_phone(phone):
    try:
        phone_number_obj = phone_parse(str(phone), "BR")
    except:
        return False
    phone = phone_number_obj.national_number
    return is_valid_number(phone_number_obj)


def sort_set(set):
    s = [set]
    s = s.sort()
    return s


def sort_dict(dict, attribute, reverse=True):
    return sorted(dict, key=lambda d: d[attribute], reverse=reverse)


### DEFAULT ###


def redirect(url):
    global domain_name
    if "url" == "home":
        url = ""
    return "<script> function openPage() { window.location.replace('" + lambda_constants["domain_name_url"] + "/redirect'); } document.onload = openPage(); </script>".replace("domain_name_url", lambda_constants["domain_name_url"]).replace("redirect", str(url))


def slugify(text):
    non_url_safe = ['"', "#", "$", "%", "&", "+", ",", "/", ":", ";", "=", "?", "@", "[", "\\", "]", "^", "`", "{", "|", "}", "~", "'"]
    translate_table = {ord(char): "" for char in non_url_safe}
    non_url_safe_regex = compile(r"[{}]".format("".join(escape(x) for x in non_url_safe)))
    non_safe = [c for c in text if c in non_url_safe]
    if non_safe:
        for c in non_safe:
            text = text.replace(c, "")
    text = "-".join(text.split())
    return text


def get_val(parameters, key):
    if key in parameters:
        return parameters[key]
    else:
        return ""


def set_attributes(self, parameters):
    for p in parameters:
        setattr(self, p, get_val(parameters, p))


def simple_html_respond(body):
    return {"statusCode": 200, "body": str(body), "headers": {"Content-Type": "text/html; charset=utf-8", "Access-Control-Allow-Origin": "*"}}


def json_res(body):
    return {"statusCode": 200, "body": dumps(body), "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}}


def respond(html, event, error_code=200):
    method = get_method_from_event(event)
    if method == "POST":
        global last_post_event
        last_post_event = event
    command = None
    if type(html) == tuple:
        command = html[1]
        user = html[2]
        html = html[0]
    try:
        try:
            response = {
                "statusCode": error_code,
                "body": html + "<div id='EVENT HERE MAN' style='display:none;'>" + dumps(event) + "<br>" + dumps(last_post_event) + "</div>",
                "headers": {"Content-Type": "text/html; charset=utf-8", "Access-Control-Allow-Origin": "*"},
            }
        except:
            response = {
                "statusCode": error_code,
                "body": html + "<div id='EVENT HERE MAN' style='display:none;'>" + dumps(event) + "</div>",
                "headers": {"Content-Type": "text/html; charset=utf-8", "Access-Control-Allow-Origin": "*"},
            }
    except:
        response = {
            "statusCode": error_code,
            "body": html,
            "headers": {"Content-Type": "text/html; charset=utf-8", "Access-Control-Allow-Origin": "*"},
        }
    if command == "login":
        response["headers"]["Set-Cookie"] = "__Secure-token=" + str(user.user_auth_token) + "; Secure; domain=" + (lambda_constants["domain_name_url"]).replace("https://encontre.", ".") + "; path=/; Max-Age=7776000;"
        response["body"] = "<script> function openPage() { window.location.replace('" + lambda_constants["domain_name_url"] + "'); } document.onload = openPage(); </script>"
    elif command == "logout":
        response["headers"]["Set-Cookie"] = "__Secure-token=; Secure; domain=" + (lambda_constants["domain_name_url"]).replace("https://encontre.", ".") + "; path=/; Max-Age=-1;"
        response["body"] = "<script> function openPage() { window.location.replace('" + lambda_constants["domain_name_url"] + "'); } document.onload = openPage(); </script>"

    if method == "GET":
        put_response_in_cache_response(event, response)

    return response


def put_response_in_cache_response(event, response):
    if event.get("cookies"):
        request_response_cache[event["requestContext"]["http"]["path"] + event["cookies"][0] + str(get_font_from_user_agent(get_user_agent_from_event(event)))] = response
    else:
        request_response_cache[event["requestContext"]["http"]["path"] + str(get_font_from_user_agent(get_user_agent_from_event(event)))] = response
    return None


def get_response_from_cache_response(event):
    if event.get("cookies"):
        if event["requestContext"]["http"]["path"] + event["cookies"][0] + str(get_font_from_user_agent(get_user_agent_from_event(event))) in request_response_cache:
            return request_response_cache[event["requestContext"]["http"]["path"] + event["cookies"][0] + str(get_font_from_user_agent(get_user_agent_from_event(event)))]
    else:
        if event["requestContext"]["http"]["path"] + str(get_font_from_user_agent(get_user_agent_from_event(event))) in request_response_cache:
            return request_response_cache[event["requestContext"]["http"]["path"] + str(get_font_from_user_agent(get_user_agent_from_event(event)))]
    return None


def check_post_fields(post={}, fields=[]):
    if not post or not fields:
        return None
    for field in fields:
        if (field not in post) or (field == None) or (field == "") or (field == " ") or (field.strip() == " ") or (field.strip() == "") or (len(field) > 500):
            return field
    return None


### UPDATE ###

### PUT ###


def put_user_email_token_into_db(user_email_token, user_email):
    check_input_data([user_email_token, user_email])
    global domain_name
    input = {
        "TableName": lambda_constants["table"],
        "Item": {
            "pk": {"S": "auth#" + str(user_email_token)},
            "sk": {"S": "auth#" + str(user_email_token)},
            "auth_user_email": {"S": str(user_email)},
            "created_at": {"S": str(int(time()))},
            "entity": {"S": "auth_token"},
        },
    }
    execute_put_item(input)
    put_user_auth_token_to_cache(user_email_token, user_email)


def put_user_auth_token_into_db(user_auth_token, user_email):
    check_input_data([user_auth_token, user_email])
    input = {
        "TableName": lambda_constants["table"],
        "Item": {
            "pk": {"S": "auth#" + str(user_auth_token)},
            "sk": {"S": "auth#" + str(user_auth_token)},
            "auth_user_email": {"S": str(user_email)},
            "created_at": {"S": str(int(time()))},
            "entity": {"S": "auth_token"},
        },
    }
    execute_put_item(input)
    put_user_auth_token_to_cache(user_auth_token, user_email)


def put_entity_into_db(entity_dict):
    execute_put_item({"TableName": lambda_constants["table"], "Item": python_obj_to_dynamo_obj(entity_dict)})


def put_dynamo_item_into_table(table, item):
    execute_put_item({"TableName": lambda_constants["table"], "Item": item})


### DELETE ###


def delete_entity_from_db(entity_dict):
    input = {"TableName": lambda_constants["table"], "Key": {"pk": {"S": str(entity_dict["pk"])}, "sk": {"S": str(entity_dict["sk"])}}}
    execute_delete_item(input)


### GET ###


def get_user_auth_token_from_db(user_auth_token):
    input = {"TableName": lambda_constants["table"], "Key": {"pk": {"S": "auth#" + str(user_auth_token)}, "sk": {"S": "auth#" + str(user_auth_token)}}}
    item = execute_get_item(input)
    if item:
        put_user_auth_token_to_cache(str(user_auth_token), item["auth_user_email"])
    return item


#########################################################################
################################# CACHE #################################
#########################################################################


form_post_cache = set()
setting_cache = {}
user_auth_token_cache = {}
user_notifications_cache = {}
user_cache = {}
request_response_cache = {}


def refresh_response_cache():
    global request_response_cache
    request_response_cache = {}


def clear_caches():
    global form_post_cache
    form_post_cache = set()
    global user_auth_token_cache
    user_auth_token_cache = {}
    global user_cache
    user_cache = {}


def show_caches_data():
    return "Auth token: " + str(user_auth_token_cache.values()) + "User: " + str(user_cache.values()) + "Event: " + str(event_cache) + "Setting: " + str(setting_cache.values())


### USER AUTH CACHE ###


def update_user_to_cache(user_email, user_dict):  # IN DB
    if not user_email:
        print("ERROR: Update user to cache " + str(user_email))
        return None
    global user_cache
    if "user_password" in user_dict:
        del user_dict["user_password"]
    user_cache[user_email] = user_dict


def get_user_from_cache(user_email):
    if not user_email:
        print("ERROR: No user_email cache request" + str(user_email))
        return None
    if user_email in user_cache:
        return user_cache[user_email]
    return None


def put_user_auth_token_to_cache(user_auth_token, user_email):  # IN DB
    if not user_auth_token or not user_email:
        print("ERROR: Update user_auth_token to cache " + str(user_auth_token))
        print("ERROR: Update user_email to cache " + str(user_email))
        return None
    global user_auth_token_cache
    user_auth_token_cache[user_auth_token] = user_email


def get_user_auth_token_from_cache(user_auth_token):
    if not user_auth_token:
        print("ERROR: No user_auth_token in cache request" + str(user_auth_token_cache))
        return None
    return user_auth_token_cache.get(user_auth_token)


#########################################################################
##########################  DEFAULT DATABASE ############################
#########################################################################


def check_input_data(input):
    if type(input) == list:
        for inputs in input:
            if inputs is None:
                print("DATABASE_ERROR: " + str(input) + " is None")
                return None
    else:
        if input is None:
            print("DATABASE_ERROR: " + str(input) + " is None")
            return None


def dynamo_obj_to_python_obj(dynamo_obj: dict) -> dict:
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in dynamo_obj.items()}


def python_obj_to_dynamo_obj(python_obj: dict) -> dict:
    serializer = TypeSerializer()
    return {k: serializer.serialize(v) for k, v in python_obj.items()}


def execute_get_item(input):
    try:
        response = dynamodb_client.get_item(**input)
        if "Item" in response:
            return dynamo_obj_to_python_obj(response["Item"])
    except ClientError as error:
        print(handle_error(error))
        return False


def execute_no_parse_get_item(input):
    try:
        response = dynamodb_client.get_item(**input)
        if "Item" in response:
            return response["Item"]
    except ClientError as error:
        print(handle_error(error))
        return False


def execute_update_item(input):
    refresh_response_cache()
    print("executing update_item")
    try:
        dynamodb_client.update_item(**input)
        return True
    except ClientError as error:
        print(handle_error(error))
        return False


def execute_query(input):
    try:
        input["ReturnConsumedCapacity"] = "TOTAL"
        response = dynamodb_client.query(**input)
        print("Consumed Capacity:" + str(response["ConsumedCapacity"]["CapacityUnits"]))
        if "Items" in response:
            deserializer_list = []
            for item in response["Items"]:
                deserializer_list.append(dynamo_obj_to_python_obj(item))
            return deserializer_list
        else:
            return response
    except ClientError as error:
        print(handle_error(error))
        return False


def execute_put_item(input):
    refresh_response_cache()
    print("executing put_item")
    try:
        dynamodb_client.put_item(**input)
        return True
    except ClientError as error:
        print(handle_error(error))
        return False


def execute_delete_item(input):
    print("executing delete_item")
    try:
        dynamodb_client.delete_item(**input)
        return True
    except ClientError as error:
        print(handle_error(error))
        return False


def handle_error(error):
    error_code = error.response["Error"]["Code"]
    error_msg = error.response["Error"]["Message"]
    error_help_string = ERROR_HELP_STRINGS[error_code]
    print("[{error_code}] {help_string}. Error message: {error_msg}".format(error_code=error_code, help_string=error_help_string, error_msg=error_msg))


ERROR_HELP_STRINGS = {
    # Common Errors
    "InternalServerError": "Internal Server Error, generally safe to retry with exponential back-off",
    "ProvisionedThroughputExceededException": "Request rate is too high. If you're using a custom retry strategy make sure to retry with exponential back-off." + "Otherwise consider reducing frequency of requests or increasing provisioned capacity for your table or secondary index",
    "ResourceNotFoundException": "One of the tables was not found, verify table exists before retrying",
    "ServiceUnavailable": "Had trouble reaching DynamoDB. generally safe to retry with exponential back-off",
    "ThrottlingException": "Request denied due to throttling, generally safe to retry with exponential back-off",
    "UnrecognizedClientException": "The request signature is incorrect most likely due to an invalid AWS access key ID or secret key, fix before retrying",
    "ValidationException": "The input fails to satisfy the constraints specified by DynamoDB, fix input before retrying",
    "RequestLimitExceeded": "Throughput exceeds the current throughput limit for your account, increase account level throughput before retrying",
}

#########################################################################
##########################  GENERATE FONT ###############################
#########################################################################


def get_font_from_user_agent(user_agent):
    from user_agents import parse

    OTF_TTF = 0
    WOOF = 1
    WOOF2 = 2

    fonts = [{"extension": "ttf", "type": "ttf"}, {"extension": "woff", "type": "woff"}, {"extension": "woff2", "type": "woff2"}]
    font_family = {}
    font_family["Chrome"] = {}
    font_family["Edge"] = {}
    font_family["Safari"] = {}
    font_family["Mobile Safari"] = {}
    font_family["Samsung Internet"] = {}
    font_family["Firefox"] = {}
    font_family["Firefox Mobile"] = {}
    font_family["Opera"] = {}
    font_family["Opera Mobile"] = {}
    font_family["IE"] = {}
    font_family["UC Browser"] = {}
    font_family["Android"] = {}
    font_family["Baiduspider"] = {}
    font_family["Chrome"]["4"] = OTF_TTF
    font_family["Chrome"]["5"] = WOOF
    font_family["Chrome"]["36"] = WOOF2
    font_family["Edge"]["12"] = WOOF
    font_family["Edge"]["14"] = WOOF2
    font_family["Safari"]["3"] = OTF_TTF
    font_family["Safari"]["5"] = WOOF
    font_family["Safari"]["12"] = WOOF2
    font_family["Mobile Safari"]["4"] = OTF_TTF
    font_family["Mobile Safari"]["5"] = WOOF
    font_family["Mobile Safari"]["10"] = WOOF2
    font_family["Samsung Internet"]["4"] = WOOF2
    font_family["Firefox"]["3"] = OTF_TTF
    font_family["Firefox"]["39"] = WOOF2
    font_family["IE"]["9"] = WOOF
    font_family["Opera"]["10"] = OTF_TTF
    font_family["Opera"]["23"] = WOOF2
    font_family["Opera Mobile"]["12"] = WOOF
    font_family["Opera Mobile"]["64"] = WOOF2
    font_family["UC Browser"]["13"] = WOOF2
    font_family["Android"]["106"] = WOOF2
    font_family["Firefox Mobile"]["106"] = WOOF2
    font_family["Baiduspider"]["13"] = WOOF2
    try:
        user_agent = parse(user_agent)
        browser_family = user_agent.browser.family
    except:
        return 0

    print(user_agent.browser.family)
    if "Chrome" in browser_family:
        browser_family = "Chrome"

    bf = font_family.get(browser_family)

    if not bf:
        return fonts[0]

    best_version = 0
    best_font = 0

    for version, font in bf.items():
        try:
            if user_agent.browser.version[0] >= int(version):
                best_version = int(version)
                best_font = font
        except:
            pass
    if best_version == 0:
        try:
            print(f"Font not found for user_agent_browser {browser_family} version {user_agent.browser.version[0]}")
        except:
            pass

    return fonts[best_font]


#########################################################################
##########################  CODE REPLACE  ###############################
#########################################################################

codes = {}


class Code:
    parts = []
    placeholders = {}
    replaced_placeholders = {}
    nested_placeholders = False
    code = ""
    common_changes = {}
    filename = None

    def __init__(self, filename=""):
        if not (path.exists("src/html/" + filename + ".html")):
            print("<p> HTML file: " + str(filename) + " not found </p> : ")
            return None
        self.filename = filename
        with open("src/html/" + filename + ".html", "r", encoding="utf-8") as read_file:
            self.code = read_file.read()
            self.clean_new_lines()
            # self.clean_double_spaces()
            self.parse()
            return None

    def clean_new_lines(self):
        self.code = self.code.replace("\n", "")

    def clean_double_spaces(self):
        self.code = self.code.replace("  ", "")
        self.code = self.code.replace("  ", "")
        self.code = self.code.replace("  ", "")
        self.code = self.code.replace("  ", "")

    def parse(self):
        self.parts = []
        self.placeholders = {}
        if "{{{{" in self.code or "}}}}" in self.code:
            self.nested_placeholders = True
        parts = self.code.split("{{")
        for part in parts:
            if part == "":
                continue
            if not "}}" in part:
                self.parts.append(part)
            else:
                placeholder_text_splited = part.split("}}")
                if len(placeholder_text_splited) == 2:
                    placeholder_text, rest = placeholder_text_splited
                else:
                    placeholder_text = placeholder_text_splited[0]
                    rest = "".join(placeholder_text_splited[1:])

                # check if placeholder is a constant
                constant = lambda_constants.get(placeholder_text.replace("_val", ""))
                if constant:
                    self.parts.append(constant)
                    self.parts.append(rest)
                    continue

                part = placeholder_text.replace("}}", "")
                part_get = self.placeholders.get(part)
                if part_get:
                    self.placeholders[part].append(len(self.parts))
                else:
                    self.placeholders[part] = [len(self.parts)]
                self.parts.append(part)
                if rest != "":
                    self.parts.append(rest)
        for common_change in self.common_changes:
            self.esc(common_change, self.common_changes[common_change])

    def esc(self, placeholder, value):
        placeholder_index = self.placeholders.get(placeholder)
        if not placeholder_index is None:
            for pi in placeholder_index:
                self.parts[pi] = str(value)
            self.placeholders[placeholder] = []
        if self.nested_placeholders and False:
            self.code = self.str_preserve_placeholders()
            self.parse()
            placeholder_indexes = self.placeholders.get(placeholder)
            if type(placeholder_indexes) == int:
                placeholder_indexes = [placeholder_indexes]
            if placeholder_indexes:
                for index in placeholder_indexes:
                    self.parts[placeholder_index]
                # del self.placeholders[placeholder]

    def str_preserve_placeholders(self):
        for placeholder_list in self.placeholders:
            for placeholder_position in self.placeholders[placeholder_list]:
                self.parts[placeholder_position] = "{{" + placeholder_list + "}}"
        return "".join(self.parts)

    def __str__(self):
        for placeholder_list in self.placeholders:

            placeholder_indexes = self.placeholders.get(placeholder_list)
            if len(placeholder_indexes) == 0:
                continue
            if self.common_changes:
                found_placeholder_in_common_changes = self.common_changes.get(placeholder_list.replace("_val", ""))
                if found_placeholder_in_common_changes:
                    self.esc(placeholder_list, found_placeholder_in_common_changes)
                    continue
                else:
                    found_placeholder_in_common_changes = self.common_changes.get(placeholder_list)
                    if found_placeholder_in_common_changes:
                        self.esc(placeholder_list, found_placeholder_in_common_changes)
                        continue

            for placeholder_position in self.placeholders[placeholder_list]:
                self.parts[placeholder_position] = ""
        return "".join(self.parts)


def read_html(filename, common_changes=None):
    global codes
    code = codes.get(filename)
    if code:
        new_code = deepcopy(code)
        new_code.common_changes = common_changes
        return new_code
    codes[filename] = Code(filename)
    new_code = deepcopy(codes[filename])
    new_code.common_changes = common_changes
    return new_code


#########################################################################
########################  CACHE WORK IN PROGRESS ########################
#########################################################################
class Cache:
    expires_in = 1000
    last_update = 0
    values = {}
    dirty = False
    values_total = 0

    def __init__(
        self,
        expires_in=1000,
    ) -> None:
        self.expires_in = expires_in
        self.dirty = False
        self.values = {}
        self.last_update = {}
        self.values_total = 0
        pass

    def set(self, key, value, update_function=None, update_params=None):
        if not key in self.values:
            self.values_total += 1
        self.values[key] = (value, time(), update_function, update_params)

    def get(self, key):
        if key in self.values:
            value, created_at, update_function, update_params = self.values[key]
            if created_at + self.expires_in > time() or self.dirty:
                if update_function:
                    value = update_function(update_params)
                    self.values[key] = (value, time(), update_function, update_params)
                else:
                    print("no update function for: " + str(key))
            return value

    def remove(self, key):
        if key in self.values:
            del self.values[key]
            self.values_total -= 1
            return True
        return False

    def __str__(self) -> str:
        return "".join(dumps(self.values))


event_cache = Cache(expires_in=5000)
