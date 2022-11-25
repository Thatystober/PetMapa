import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from json import load, dumps
from pages.page import s3_client, lambda_constants, ses_client, read_html, generate_area_cases, generate_suggestion_score, get_user_with_email_from_db, generate_image
import traceback


def list_html_email_suggestion_item(area_cases, send_email_count):
    full_html = ""
    for index in range(send_email_count):
        html = read_html("case/_codes/email_suggestion_item")
        html.esc("case_photo_val", generate_image(area_cases[index]["case_photo"], "200", "200"))
        html.esc("case_lat_val", area_cases[index]["case_lat"])
        html.esc("case_lon_val", area_cases[index]["case_lon"])
        full_html += str(html)
    return full_html


def send_email_to_top_area_cases(current_case, area_cases):
    send_email_count = 0
    if area_cases:
        for index, case in enumerate(area_cases):
            if case["case_similarity"] >= 0.5:
                send_email_count += 1

                # if os.environ.get("AWS_EXECUTION_ENV") is None:
                #     pdf_path = "tmp/talvez_seja_seu_pet" + (str(index + 1)) + ".pdf"
                # else:
                #     pdf_path = "/tmp/talvez_seja_seu_pet" + (str(index + 1)) + ".pdf"
                # s3_client.download_file(lambda_constants["img_bucket"], "pdf_" + case["case_id"] + ".pdf", pdf_path)

    if send_email_count > 0:
        user = get_user_with_email_from_db(current_case["case_email"])
        html = read_html("case/_codes/email")
        html.esc("html_email_suggestion_item", list_html_email_suggestion_item(area_cases, send_email_count))
        html.esc("user_name_val", user["user_name"].title())
        ### SENDING EMAIL WITH ATTACHMENT ###
        if current_case["case_status"] == "lost":
            html.esc("email_title_message", "Acho que encontramos o seu pet")
            subject = "É possível que nós tenhamos encontrado o(a) " + current_case["case_name"].title() + "."
        if current_case["case_status"] == "found":
            subject = "É possível que nós tenhamos encontrado  um(a) dono para o seu pet" + current_case["case_name"].title() + "."
            html.esc("email_title_message", "Acho que encontramos o dono do pet")

        # SENDER = "nao-responda@" + lambda_constants["domain_name"] + ".com.br"
        SENDER = "suporte@petmapa.com.br"
        RECEIVER = current_case["case_email"]
        CHARSET = "utf-8"
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = SENDER
        msg["To"] = RECEIVER
        msg_body = MIMEMultipart("alternative")
        # text based email body
        BODY_TEXT = subject
        # HTML based email body
        BODY_HTML = str(html)
        textpart = MIMEText(BODY_TEXT.encode(CHARSET), "plain", CHARSET)
        htmlpart = MIMEText(BODY_HTML.encode(CHARSET), "html", CHARSET)
        msg_body.attach(textpart)
        msg_body.attach(htmlpart)
        msg.attach(msg_body)

        # Full path to the file that will be attached to the email.
        if os.environ.get("AWS_EXECUTION_ENV") is None:
            ATTACHMENT1 = "tmp/talvez_seja_seu_pet1.pdf"
        else:
            ATTACHMENT1 = "/tmp/talvez_seja_seu_pet1.pdf"

        # att1 = MIMEApplication(open(ATTACHMENT1, "rb").read())
        # att1.add_header("Content-Disposition", "attachment", filename=os.path.basename(ATTACHMENT1))
        # msg.attach(att1)

        # if send_email_count > 1:
        #     if os.environ.get("AWS_EXECUTION_ENV") is None:
        #         ATTACHMENT2 = "tmp/talvez_seja_seu_pet2.pdf"
        #     else:
        #         ATTACHMENT2 = "/tmp/talvez_seja_seu_pet2.pdf"
        #     att2 = MIMEApplication(open(ATTACHMENT2, "rb").read())
        #     att2.add_header("Content-Disposition", "attachment", filename=os.path.basename(ATTACHMENT2))
        #     msg.attach(att2)

        # if send_email_count > 2:
        #     if os.environ.get("AWS_EXECUTION_ENV") is None:
        #         ATTACHMENT3 = "tmp/talvez_seja_seu_pet3.pdf"
        #     else:
        #         ATTACHMENT3 = "/tmp/talvez_seja_seu_pet3.pdf"
        #     att3 = MIMEApplication(open(ATTACHMENT3, "rb").read())
        #     att3.add_header("Content-Disposition", "attachment", filename=os.path.basename(ATTACHMENT3))
        #     msg.attach(att3)

        try:
            response = ses_client.send_raw_email(
                Source=SENDER,
                Destinations=[RECEIVER],
                RawMessage={
                    "Data": msg.as_string(),
                },
                ConfigurationSetName=lambda_constants["domain_name"],
            )
            print("Message id : ", response["MessageId"])
            print("Message send successfully!")
        except Exception as e:
            print("Error: ", e)
    return


def lambda_handler(event, context):
    print(dumps(event))
    try:
        return main_lambda_handler(event, context)
    except Exception as e:
        send_error_email(event, e)
        return


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


def main_lambda_handler(event, context):
    path = {}
    path["case"] = event.get("current_case")
    area_cases = generate_area_cases(path["case"]["case_lat"], path["case"]["case_lon"], path["case"]["case_type"], path["case"]["case_id"], path["case"]["case_status"])
    if area_cases:
        area_cases = generate_suggestion_score(path["case"], area_cases)
        send_email_to_top_area_cases(path["case"], area_cases)
    return


if os.environ.get("AWS_EXECUTION_ENV") is None:
    with open("_testnow.json", "r") as read_file:
        event = load(read_file)
        html = main_lambda_handler(event, None)
    f = open("test_html.html", "w")
    f.write(html.get("body"))
    f.close()
