import sys
import os
import json
from uuid import uuid4
from base64 import b64decode, b64encode
from urllib.parse import parse_qs
from time import time
import qrcode
from PIL import Image
from io import BytesIO
import pdfkit

sys.path.append("/".join(str(os.path.join(os.path.dirname(__file__))).split("/")[:-1]))

from utils.utils import (
    Code,
    lambda_constants,
    sqs_client,
    ses_client,
    lambda_client,
    sesv2_client,
    temp_s3_client,
    s3_client,
    form_post_cache,
    execute_update_item,
    refresh_response_cache,
    get_font_from_user_agent,
    validate_date,
    validate_email,
    execute_no_parse_get_item,
    simple_html_respond,
    json_res,
    redirect,
    check_image_exists,
    get_user_agent_from_event,
    delete_entity_from_db,
    validate_br_phone,
    validate_legal_id,
    validate_legal_cnpj,
    format_to_brl_money,
    format_to_cnpj,
    format_to_cpf,
    validate_password,
    check_if_mobile_from_event,
    check_post_fields,
    execute_query,
    format_unixtime_to_HM_time,
    execute_put_item,
    slugify,
    put_entity_into_db,
    encode_to_b64,
    get_first_param_in_raw_path,
    get_user_auth_token_from_cache,
    get_user_auth_token_from_db,
    get_user_ip_from_event,
    get_url_from_event,
    format_to_mobile_phone_number,
    sort_dict,
    read_html,
    decode_from_b64,
    execute_get_item,
)
from objects.user import get_user_password_into_crypto_data_base, put_user_password_into_crypto_data_base
from objects.user import User, get_user_from_event
from objects.case import Case


class Page:
    route = ""
    html_code_original = ""
    required_parameters = []
    bypass = False
    public = True

    def __init__(self, route="", html_file="", bypass=False, public=True) -> None:
        self.route = route
        self.html_code_original = read_html(html_file)
        if self.html_code_original is None:
            print("Nao consegui ler code da pagina: " + html_file)
        self.html_file = html_file
        self.bypass = bypass
        self.public = public


def parse_html(html_file, route="", path="", event="", user=None, common_changes={}):
    html = read_html(html_file, common_changes)
    font_format = get_font_from_user_agent(get_user_agent_from_event(event))
    header_code = read_html("main/header", common_changes)
    header_code.esc("font_ext_val", font_format["extension"])
    header_code.esc("font_type_val", font_format["type"])
    html.esc("header", str(header_code))
    footer_code = read_html("main/footer", common_changes)
    html.esc("footer", str(footer_code))
    menu_code = read_html("main/menu", common_changes)
    if route == "login" or route == "register" or route == "register_password" or route == "password" or route == "password_reset" or route == "profile":
        menu_code.esc("profile_active_val", "active")
    elif route == "profile" or route == "profile_edit" or route == "profile_password" or route == "profile_my_cases" or route == "profile_case" or route == "lost_form_edit":
        menu_code.esc("profile_active_val", "active")
    elif route == "found" or route == "found_model" or route == "found_form" or route == "found_map" or route == "found_suggestion" or route == "found_case":
        menu_code.esc("found_active_val", "active")
    elif route == "home":
        menu_code.esc("home_active_val", "active")
    elif route == "lost" or route == "lost_model" or route == "lost_form" or route == "lost_map" or route == "lost_suggestion" or route == "lost_case":
        menu_code.esc("lost_active_val", "active")
    elif route == "donation":
        menu_code.esc("donation_active_val", "active")
    html.esc("menu", str(menu_code))
    html.esc("user_url_val", get_url_from_event(event))
    return html


def check_error_msg(html, error_msg=""):
    if error_msg:
        html.esc("error_msg_val", error_msg.capitalize() + ".")
        html.esc("error_msg_visibility_val", "")
        return True
    else:
        html.esc("error_msg_val", "")
        html.esc("error_msg_visibility_val", "display:none;")
        return False


def translate_size(size):
    if size.lower() == "p":
        return "pequeno"
    if size.lower() == "m":
        return "médio"
    if size.lower() == "g":
        return "grande"


def translate_date(date):
    try:
        return date.split("-")[2] + "/" + date.split("-")[1] + "/" + date.split("-")[0]
    except:
        return date


def translate_age_time(age_time):
    if age_time.lower() == "month":
        return "Mes(es)"
    if age_time.lower() == "year":
        return "Ano(s)"


def insert_image_form_data(prefix_name, html):
    file_name = str(uuid4())
    response = temp_s3_client.generate_presigned_post(lambda_constants["img_bucket"], file_name, ExpiresIn=3600)
    html.esc(prefix_name + "_image_file_val", file_name)
    html.esc(prefix_name + "_s3_post_url_val", response["url"])
    html.esc(prefix_name + "_key_val", response["fields"]["key"])
    html.esc(prefix_name + "_AWSAccessKeyId_val", response["fields"]["AWSAccessKeyId"])
    html.esc(prefix_name + "_policy_val", response["fields"]["policy"])
    html.esc(prefix_name + "_signature_val", response["fields"]["signature"])
    return html


def generate_image(img_name, width, height):
    request = {"bucket": lambda_constants["img_bucket"]}
    request["key"] = img_name
    request["edits"] = {"resize": {"width": width, "height": height, "fit": "cover"}}
    return encode_to_b64(str(json.dumps(request)))


def generate_qr_code(code, cdn, name=None):
    qrPIL = qrcode.make(code)
    qrPIL = qrPIL.resize((int(300), int(300)), Image.NEAREST)
    buffer = BytesIO()
    qrPIL.save(buffer, "PNG")
    if os.environ.get("AWS_EXECUTION_ENV") is None:
        qrPIL.save("tmp/qrcode.PNG")
    else:
        qrPIL.save("/tmp/qrcode.PNG")
    buffer.seek(0)
    if not name:
        name = code
    temp_s3_client.put_object(Body=buffer, Bucket=cdn, ContentType="image/png", Key="qr_" + name + ".png")
    return buffer


def generate_pdf(case_id):
    pdf_path = "/tmp/case_pdf.pdf"
    PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf="/opt/bin/wkhtmltopdf")
    pdfkit.from_url(lambda_constants["domain_name_url"] + "/case/" + case_id, pdf_path, configuration=PDFKIT_CONFIG)
    s3_client.upload_file(Filename=pdf_path, Bucket=lambda_constants["img_bucket"], Key="pdf_" + case_id + ".pdf")
    return True


def generate_area_cases(case_lat, case_lon, case_type, case_id, case_status):
    all_area_cases = []
    area_lat_sign = case_lat[0]
    area_lon_sign = case_lon[0]
    area_lat_float = float(case_lat[1:])
    area_lon_float = float(case_lon[1:])
    query_areas = [
        area_lat_sign + str(area_lat_float - 0.02)[:5] + area_lon_sign + str(area_lon_float - 0.02)[:5],
        area_lat_sign + str(area_lat_float - 0.01)[:5] + area_lon_sign + str(area_lon_float - 0.02)[:5],
        area_lat_sign + str(area_lat_float)[:5] + area_lon_sign + str(area_lon_float - 0.02)[:5],
        area_lat_sign + str(area_lat_float + 0.01)[:5] + area_lon_sign + str(area_lon_float - 0.02)[:5],
        area_lat_sign + str(area_lat_float + 0.02)[:5] + area_lon_sign + str(area_lon_float - 0.02)[:5],
        area_lat_sign + str(area_lat_float - 0.02)[:5] + area_lon_sign + str(area_lon_float - 0.01)[:5],
        area_lat_sign + str(area_lat_float - 0.02)[:5] + area_lon_sign + str(area_lon_float)[:5],
        area_lat_sign + str(area_lat_float - 0.02)[:5] + area_lon_sign + str(area_lon_float + 0.01)[:5],
        area_lat_sign + str(area_lat_float - 0.02)[:5] + area_lon_sign + str(area_lon_float + 0.02)[:5],
        area_lat_sign + str(area_lat_float - 0.01)[:5] + area_lon_sign + str(area_lon_float + 0.02)[:5],
        area_lat_sign + str(area_lat_float)[:5] + area_lon_sign + str(area_lon_float + 0.02)[:5],
        area_lat_sign + str(area_lat_float + 0.01)[:5] + area_lon_sign + str(area_lon_float + 0.02)[:5],
        area_lat_sign + str(area_lat_float + 0.02)[:5] + area_lon_sign + str(area_lon_float + 0.02)[:5],
        area_lat_sign + str(area_lat_float + 0.02)[:5] + area_lon_sign + str(area_lon_float - 0.01)[:5],
        area_lat_sign + str(area_lat_float + 0.02)[:5] + area_lon_sign + str(area_lon_float)[:5],
        area_lat_sign + str(area_lat_float + 0.02)[:5] + area_lon_sign + str(area_lon_float + 0.01)[:5],
        area_lat_sign + str(area_lat_float - 0.01)[:5] + area_lon_sign + str(area_lon_float - 0.01)[:5],
        area_lat_sign + str(area_lat_float - 0.01)[:5] + area_lon_sign + str(area_lon_float)[:5],
        area_lat_sign + str(area_lat_float - 0.01)[:5] + area_lon_sign + str(area_lon_float + 0.01)[:5],
        area_lat_sign + str(area_lat_float)[:5] + area_lon_sign + str(area_lon_float - 0.01)[:5],
        area_lat_sign + str(area_lat_float)[:5] + area_lon_sign + str(area_lon_float)[:5],
        area_lat_sign + str(area_lat_float)[:5] + area_lon_sign + str(area_lon_float + 0.01)[:5],
        area_lat_sign + str(area_lat_float + 0.01)[:5] + area_lon_sign + str(area_lon_float - 0.01)[:5],
        area_lat_sign + str(area_lat_float + 0.01)[:5] + area_lon_sign + str(area_lon_float)[:5],
        area_lat_sign + str(area_lat_float + 0.01)[:5] + area_lon_sign + str(area_lon_float + 0.01)[:5],
    ]
    for area in query_areas:
        area_cases = query_cases_from_area(area)
        if area_cases:
            for case in area_cases:
                if case["case_type"] == case_type:
                    if case["case_id"] != case_id:
                        if case["case_status"] == "found" and case_status == "lost":
                            all_area_cases.append(case)
                        elif case["case_status"] == "lost" and case_status == "found":
                            all_area_cases.append(case)
    return all_area_cases


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
    area_cases = sort_dict(area_cases, "created_at", True)
    area_cases = sort_dict(area_cases, "case_similarity", True)
    return area_cases


def send_emails_to_similar_cases(area_cases):
    if area_cases:
        for case in area_cases:
            if case["case_similarity"] >= 0.5:
                response = invoke_send_case_email(case)
    return


def invoke_send_case_email(current_case):
    return lambda_client.invoke(FunctionName="arn:aws:lambda:sa-east-1:334053983103:function:send_case_email", InvocationType="Event", Payload=json.dumps({"current_case": current_case}))


#####################################################################################################################################################################################
##### GET OBJETCTS ######### GET OBJETCTS ######### GET OBJETCTS ######### GET OBJETCTS ######### GET OBJETCTS ######### GET OBJETCTS ######### GET OBJETCTS ######### GET OBJETCTS #
#####################################################################################################################################################################################
def get_case_from_db(case_id):
    query = execute_query({"TableName": "petmapa", "IndexName": "sk-pk-index", "KeyConditionExpression": "#766a0 = :766a0", "ExpressionAttributeNames": {"#766a0": "sk"}, "ExpressionAttributeValues": {":766a0": {"S": "case#" + case_id}}})
    if query:
        return query[0]
    return None


def get_user_with_email_from_db(user_email):
    item = execute_get_item({"TableName": "petmapa", "Key": {"pk": {"S": "user#" + user_email}, "sk": {"S": "user#" + user_email}}})
    if item:
        return item
    return None


def query_cases_from_area(area):
    query = execute_query({"TableName": "petmapa", "IndexName": "case_area-sk-index", "KeyConditionExpression": "#766a0 = :766a0", "ExpressionAttributeNames": {"#766a0": "case_area"}, "ExpressionAttributeValues": {":766a0": {"S": area}}})
    if query:
        return query
    return []


def query_all_cases():
    query = execute_query({"TableName": "petmapa", "IndexName": "entity-created_at-index", "KeyConditionExpression": "#766a0 = :766a0", "ExpressionAttributeNames": {"#766a0": "entity"}, "ExpressionAttributeValues": {":766a0": {"S": "case"}}})
    if query:
        return query
    return []


def query_all_user_cases(user_email):
    query = execute_query({"TableName": "petmapa", "KeyConditionExpression": "#bef90 = :bef90 And begins_with(#bef91, :bef91)", "ExpressionAttributeNames": {"#bef90": "pk", "#bef91": "sk"}, "ExpressionAttributeValues": {":bef90": {"S": "user#" + user_email}, ":bef91": {"S": "case#"}}})
    if query:
        return query
    return []


def update_case_phone(case):
    return execute_update_item({"TableName": "petmapa", "Key": {"pk": {"S": case["pk"]}, "sk": {"S": case["sk"]}}, "UpdateExpression": "SET #60aa0 = :60aa0", "ExpressionAttributeNames": {"#60aa0": "case_phone"}, "ExpressionAttributeValues": {":60aa0": {"S": case["case_phone"]}}})


#########################################################################################################################################################################################
##### POST ######### POST ######### POST ######### POST ######### POST ######### POST ######### POST ######### POST ######### POST ######### POST ######### POST ######### POST #########
#########################################################################################################################################################################################


def get_post_data(event, post):
    if "body" in event:
        if event["isBase64Encoded"] == True:
            parameters = parse_qs(str(b64decode(event["body"]).decode("utf-8")))
            for param in parameters:
                post[param] = parameters[param][0]
        else:
            post = json.loads(event["body"])
        if "form_id" in post:
            if post["form_id"] not in form_post_cache:
                form_post_cache.add(post["form_id"])
                del post["form_id"]
                return post
            else:
                return {}
        return post
    return {}


#########################################################################################################################################################################################
##### PATH ######### PATH ######### PATH ######### PATH ######### PATH ######### PATH ######### PATH ######### PATH ######### PATH ######### PATH ######### PATH ######### PATH #########
#########################################################################################################################################################################################


def get_path_data(path, event, user_email=None, data_base=False):
    if "ERROR" in path:
        del path["ERROR"]

    if "user_email_token" in path:
        if not path["user_email_token"]:
            path["ERROR"] = "Nenhum token encodado encontrado"
            return path

    if "case_id" in path:
        if not path["case_id"]:
            path["ERROR"] = "Nenhum caso encontrado"
            return path
        path["case"] = get_case_from_db(path["case_id"])
        if not path["case"]:
            path["ERROR"] = "Nenhum caso encontrado"
            return path

    if "user_email_encoded" in path:
        if not path["user_email_encoded"]:
            path["ERROR"] = "Email de usuário não encontrado"
            return path
        path["user_email"] = decode_from_b64(path["user_email_encoded"])
        if not path["user_email"]:
            print("ERROR: No user_email found")
            path["ERROR"] = "Email de usuário não encontrado"
            return path

    if "user_auth_token" in path:
        if not path["user_auth_token"]:
            path["ERROR"] = "Token de usuário não encontrado"
            return path
        # path["user"] = User()
        # path["user"].get_user_with_auth_token(path["user_auth_token"])
        # if not path["user"].user_valid:
        #     path["ERROR"] = "Token de usuário não encontrado"
        #     return path

    if "case_type" in path:
        if not path["case_type"]:
            path["ERROR"] = "Tipo de animal inválido"
            return path
        if path["case_type"] != "dog" and path["case_type"] != "cat":
            path["ERROR"] = "Tipo de animal inválido"
            return path

    if "case_model" in path:
        if not path["case_model"]:
            path["ERROR"] = "Tipo de modelo inválido"
            return path
        case_types = path["case_model"].split("-")
        for type in case_types:
            if type != "model1" and type != "model2" and type != "model3" and type != "model4" and type != "model5" and type != "model6" and type != "model7" and type != "model8" and type != "model9" and type != "model10" and type != "model11" and type != "model12":
                path["ERROR"] = "Tipo de modelo inválido"
                return path

    path["current_page"] = get_first_param_in_raw_path(event)
    path["user_ip"] = get_user_ip_from_event(event)
    # path["user_region"] = get_user_country_region(path["user_ip"])
    path["url"] = get_url_from_event(event)

    return path
