import db
import json
import psycopg2.extras
from anomaly_user import AnomalyUser
from google_analytics_user import GoogleAnalyticsUser


def get_anomalies():
    with db.con:
        cursor = db.con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM anomaly WHERE SENT = FALSE")

        anomaly_list = []
        for row in cursor:
            # TODO: Check if we can just append the row
            anomaly_list.append({
                'date': row[0],
                'reason': row[1],
                'user_id': row[2],
                'account_id': row[3],
                'property_id': row[4],
                'view_id': row[5],
                'sent': row[6]})

        result = anomaly_list
        return result


def send_mails():
    my_detection_list = get_anomalies()

    for anomaly in my_detection_list:
        current_user = AnomalyUser.get(anomaly['user_id'])
        my_ga_user = GoogleAnalyticsUser(token=json.loads(current_user.code))

        # GETTING NAMES OF CURRENT ACCOUNT, PROPERTY, VIEW SHOULD BE PART OF GA LOADER

        mail_subject = "New Anomaly Detection - " + str(anomaly['date'])
        mail_body = "Dear Anomaly Detection User,\n\nOn " + str(anomaly['date']) \
                    + " we detected an anomaly in your data. " \
                    + "We observed: " + anomaly['reason'] \
                    + ". The observation was made for the following environment:\n\n"

        # add account name
        account_list = my_ga_user.get_account_names()
        mail_body += "Account: " + account_list[anomaly['account_id']] + "\n"

        # add property name
        property_list = my_ga_user.get_property_names(selected_account=anomaly['account_id'])
        mail_body += "Property: " + property_list[anomaly['property_id']] + "\n"

        # add view name
        view_list = my_ga_user.get_view_names(
            selected_account=anomaly['account_id'],
            selected_property=anomaly['property_id']
        )
        if view_list:
            mail_body += "View: " + view_list[anomaly['view_id']] + "\n"

        mail_body += "\nBest regards,\nYour Cross Platform Solutions Team"

        # TODO: send mail
        print(mail_subject)
        print(mail_body)

        # TODO: set anomaly to sent -> might require an anomaly id in the database


send_mails()
