from engine.error import InternalError, VisibleError
from typing import Any, Callable, Dict
import gspread
import gspread
from gspread.exceptions import APIError
from time import sleep
import json
import glob

# Use this to get a service key and save it into keys/google-service-accounts/credentials.json.
# https://docs.gspread.org/en/latest/oauth2.html

# Code ported from CS 61C Total Course Points
# https://github.com/61c-teach/TotalCoursePoints/blob/master/TotalCoursePoints/utils.py

# we want to wait 10 seconds before we try to do the request.
GSPREAD_TIMEOUT = 10

# <= 0 means we will try till success. otherwise a positive value.
GSPREAD_ATTEMPTS = 500

RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"


class ResourceExhaustedError(Exception):
    pass


class SheetsAPI:

    SCOPE = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    def __init__(self, credentials_dir: str) -> None:
        self.clients = []
        self.credentials_dir = credentials_dir


    def get_clients(self):
        for i, cred in enumerate(glob.glob(self.credentials_dir + '*.json')):
            if i <= len(self.clients):
                self.clients.append(gspread.service_account(filename=cred))
            yield self.clients[i]

    def call(self, method: Callable):
        i = 0
        def should_retry(): return GSPREAD_ATTEMPTS <= 0 or i < GSPREAD_ATTEMPTS

        def attempt(client):
            raise_error = None
            try:
                return method(client)
            except APIError as e:
                raise_error = e

            if raise_error is not None:
                e: Exception = raise_error
                raise_resource_error = False
                try:
                    if json.loads(e.response.text)["error"]["status"] == RESOURCE_EXHAUSTED:
                        raise_resource_error = True
                    else:
                        raise e
                except Exception:
                    raise e
                if raise_resource_error:
                    raise ResourceExhaustedError()

        while should_retry():
            j = 0
            for client in self.get_clients():
                try:
                    return attempt(client)
                except ResourceExhaustedError:
                    print(f"Failed to use client {j}, trying a new one...")
                j += 1
            i += 1
            print(f"The resources have been exhausted (attempt: {i - 1})!" +
                  (f" Retrying in {GSPREAD_TIMEOUT} seconds..." if should_retry() else ""))
            if should_retry():
                sleep(GSPREAD_TIMEOUT)

        raise InternalError("Failed - resource exhaustion.")


def fetch_student_record(credentials_dir: str, student_id: str, spreadsheet_url: str, worksheet_index: int = 0) -> Dict[str, Any]:
    """
    Fetches record with matching ID from sheet.
    """
    endpoint = SheetsAPI(credentials_dir=credentials_dir)

    def fetch(client: gspread.Client):
        ss: gspread.Spreadsheet = client.open_by_url(url=spreadsheet_url)
        ws = ss.get_worksheet(worksheet_index)
        cell = ws.find(query=str(student_id))
        if cell:
            row_index: int = cell.row
            headers = ws.row_values(1)
            row = ws.row_values(row_index)
            record = {}
            for i, header in enumerate(headers):
                record[header] = row[i]
            return record
        else:
            raise VisibleError(f"Student ID {student_id} not found.")

    return endpoint.call(fetch)
