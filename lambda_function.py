import os
from pages.page_manager import PageManager
from json import dumps, load
from pages.page import get_path_data, get_post_data, get_user_from_event
from utils.utils import ses_client, lambda_constants, get_response_from_cache_response, get_method_from_event, get_path_from_event, respond, redirect
from time import time
import traceback

last_cache_clear = time()
page_manager = PageManager()


def get_page_from_event(event, method):
    if "rawPath" in event:
        try:
            route = event["rawPath"].split("/")[1]
            if method == "GET":
                if route == "":
                    return page_manager.pages_get["home"]
                elif route in page_manager.pages_get:
                    return page_manager.pages_get[route]
            elif method == "POST":
                if route == "":
                    return page_manager.pages_get["home"]
                elif route in page_manager.pages_post:
                    return page_manager.pages_post[route]
            return None
        except:
            return None
    return None


def lambda_handler(event, context):
    try:
        return main_lambda_handler(event, context)
    except Exception as e:
        send_error_email(event, e)
        path = get_path_data(get_path_from_event(event), event)
        post = {}
        return respond(page_manager.pages_get["not_found"].get(event, path, post, "infelizmente um erro aconteceu, já enviamos um relatório para o suporte e brevemente ele será solucionado", None), event)


def main_lambda_handler(event, context):
    method = get_method_from_event(event)
    if method != "GET" and method != "POST":
        return respond("", event)
    if method == "GET":
        response_from_cache = get_response_from_cache_response(event)
        if response_from_cache:
            return response_from_cache

    page = get_page_from_event(event, method)
    ### SHOW PAGE IN INVOKER ###
    if page:
        print(dumps(method) + " -> " + str(dumps(page.route)) + " -> " + dumps(event))
    user = get_user_from_event(event)

    ### CLEAR CACHES ###
    # global last_cache_clear
    # if time() > (last_cache_clear + 10):
    #     clear_caches()

    # ### REDIRECT TO ANOTHER LAMBDAS ###
    # if page is None:
    #     project = get_second_param_in_raw_path(event)
    #     if project:
    #         print(dumps(method) + " -> " + dumps(project) + " -> " + dumps(event))
    #         if project == "get_queue_position":
    #             return lambda_get_queue_position(event, user)
    #         if project == "get_reception_queue":
    #             return lambda_get_reception_queue(event, user)

    path = get_path_data(get_path_from_event(event), event)
    post = {}

    if "ERROR" in path:
        return respond(page_manager.pages_get["not_found"].get(event, path, post, path["ERROR"], user), event)
    if not user and not page.public:
        return respond(redirect("login/must_be_logged_in"), event)
    if user and page.bypass:
        return respond(redirect(""), event)
    if method == "GET":
        return respond(page.get(event, path, post, None, user), event)
    if method == "POST":
        post = get_post_data(event, post)
        return respond(page.post(event, path, post, None, user), event)


def send_error_email(event, e):
    tb = traceback.format_exc()
    html = "LAMBDA ERROR IN PETMAPA: " + str(e) + "\n\n<br><br> TRACEBACK: " + tb + "\n\n<br><br> EVENT: " + dumps(event)
    ses_client.send_email(
        Destination={"ToAddresses": ["eugenio@devesch.com.br"]},
        Message={
            "Body": {
                "Html": {
                    "Charset": "utf-8",
                    "Data": str(html),
                },
                "Text": {
                    "Charset": "utf-8",
                    "Data": str(html),
                },
            },
            "Subject": {
                "Charset": "utf-8",
                "Data": "LAMBDA ERROR IN PETMAPA",
            },
        },
        Source="eugenio@devesch.com.br",
        ConfigurationSetName=lambda_constants["domain_name"],
    )
    return


if os.environ.get("AWS_EXECUTION_ENV") is None:
    with open("_testnow.json", "r") as read_file:
        event = load(read_file)
        html = main_lambda_handler(event, None)
    f = open("test_html.html", "w")
    f.write(html.get("body"))
    f.close()
    import webbrowser

    webbrowser.open("file://" + os.path.realpath(os.getcwd() + "/test_html.html"))
    print("END")
