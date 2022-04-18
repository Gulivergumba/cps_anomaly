import db, json
import psycopg2.extras
from anomaly_user import AnomalyUser
import google_analytics_user

class anomaly_class():
    def __init__(self, date, reason, user_id, account_id, property_id, view_id, sent=False):
        
        self.date = date
        self.reason = reason
        self.user_id = user_id
        self.account_id = account_id
        self.property_id = property_id
        self.view_id = view_id
        self.sent = sent


class detections():
    def __init__(self, anomaly_list=[]):
        self.anomaly_list=anomaly_list

    @staticmethod
    def get_anomalies():
        with db.con:
            cursor = db.con.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT * FROM anomaly WHERE SENT = FALSE")

            anomaly_list = []
            for row in cursor:
                 anomaly_list.append(anomaly_class(row[0],row[1],row[2],row[3],row[4],row[5],row[6]))
            
            result = detections(anomaly_list)
            return result


def send_mails():
    my_detections = detections.get_anomalies()
    
    for anomaly in my_detections.anomaly_list:
        current_user = AnomalyUser.get(anomaly.user_id)
        my_ga_user = ga_loader.GoogleAnalyticsUser(token=json.loads(current_user.code))
        
        #GETTING NAMES OF CURRENT ACCOUNT, PROPERTY, VIEW SHOULD BE PART OF GA LOADER

        mail_subject = "New Anomaly Detection - "+str(anomaly.date)
        mail_body = "Dear Anomaly Detection User,\n\nOn "+str(anomaly.date)+" we detected an anomaly in your data. "
        mail_body += "We observed: "+anomaly.reason+". The observation was made for the following environment:\n\n"

        # add account name 
        my_ga_user.set_account_list()
        account_list = my_ga_user.get_account_names()
        mail_body += "Account: "+account_list[anomaly.account_id]+"\n"

        # add property name
        my_ga_user.set_property_list(anomaly.account_id)
        property_list = my_ga_user.get_property_names()
        mail_body += "Property: "+property_list[anomaly.property_id]+"\n"

        # add view name
        my_ga_user.set_view_list(anomaly.property_id)
        view_list = my_ga_user.get_view_names()
        if view_list:
            mail_body += "View: "+view_list[anomaly.view_id]+"\n"


        mail_body += "\nBest regards,\nYour Cross Platform Solutions Team"

        #TODO: send mail 
        print(mail_subject)
        print(mail_body)

send_mails()
