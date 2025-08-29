# modules/crm.py
import csv
import os
import pandas as pd

from . import ModuleBase


class CRMModule(ModuleBase):
    name = "crm"
    title = "CRM и сегменты"

    def export_csv(self, path="static/export/users.csv"):
        users = self.services["db"].list_users(limit=100000)
        keys = list(users[0].keys()) if users else ["user_id", "first_seen", "messages_count", "last_action",
                                                    "attributes"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for u in users: w.writerow(u)
        return "/" + path

    def export_xlsx(self, path="static/export/users.xlsx"):
        os.makedirs("static/export", exist_ok=True)
        users = self.services["db"].list_users(limit=100000)
        df = pd.DataFrame(users)
        df.to_excel(path, index=False)
        return "/" + path
