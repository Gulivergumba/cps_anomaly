import db
import json
from smtplib import SMTP_SSL, SMTPException
import psycopg2.extras
from anomaly_user import AnomalyUser
from google_analytics_user import GoogleAnalyticsUser
import google_analytics_config as google_config


def get_anomalies_no_mail_sent():
    with db.con:
        cursor = db.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM anomaly WHERE SENT = FALSE")

        send_mail_list = []
        for row in cursor:
            if not row["sent"]:
                send_mail_list.append(row)

        result = send_mail_list
        return result


def set_anomaly_to_mail_sent(anomaly_id):
    with db.con:
        cursor = db.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"UPDATE anomaly SET SENT = TRUE WHERE anomaly_id = {anomaly_id}")


def get_email_address(account_id):
    with db.con:
        cursor = db.con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"SELECT email FROM users WHERE CAST(id AS INTEGER) = {account_id}")
        for row in cursor:
            return row['email']
        return None


def send_email(receipient, subject, body):
    message = f"""From: Cross Platform Solutions GmbH <{google_config.google_mail_user}>
To: <{receipient[0]}>
Subject: {subject}

{body}
"""
    with SMTP_SSL('smtp.gmail.com', 465) as smtp:
        try:
            smtp.login(user=google_config.google_mail_user, password=google_config.google_mail_password)
            smtp.sendmail(from_addr=google_config.google_mail_user, to_addrs=receipient, msg=message)

        except SMTPException:
            return False
    return True


def main():
    send_mail_list = get_anomalies_no_mail_sent()

    number_of_mails_sent = 0
    for anomaly in send_mail_list:
        current_user = AnomalyUser.get(anomaly['user_id'])
        my_ga_user = GoogleAnalyticsUser(token=json.loads(current_user.code))

        # GETTING NAMES OF CURRENT ACCOUNT, PROPERTY, VIEW SHOULD BE PART OF GA LOADER
        account_list = my_ga_user.get_account_names()
        property_list = my_ga_user.get_property_names(selected_account=anomaly['account_id'])
        view_list = my_ga_user.get_view_names(
            selected_account=anomaly['account_id'],
            selected_property=anomaly['property_id']
        )

        email_subject = f"New Anomaly Detection - {anomaly['date']}"
        email_body = f"Dear Anomaly Detection User,\n\nOn {anomaly['date']} we detected an anomaly in your data. " \
                     f"We observed: {anomaly['reason']}. The observation was made for the following environment:\n\n" \
                     f"Account: {account_list[anomaly['account_id']]}\n" \
                     f"Property: {property_list[anomaly['property_id']]}\n"
        if view_list:
            email_body += f"View: {view_list[anomaly['view_id']]}\n"
        email_body += "\nBest regards,\nYour Cross Platform Solutions Team"

        email = get_email_address(anomaly['account_id'])
        if send_email(receipient=[email], subject=email_subject, body=email_body):
            set_anomaly_to_mail_sent(anomaly['anomaly_id'])
            number_of_mails_sent += 1
    if number_of_mails_sent > 0:
        print(f"Successfully sent {number_of_mails_sent} mail(s).")
    else:
        print("No emails needed to be sent.")

if __name__ == '__main__':
    main()
