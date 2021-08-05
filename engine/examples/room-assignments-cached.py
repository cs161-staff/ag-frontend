from engine.extensions.cached_sheets.main import CachedSheetPlugin
from engine.extensions.sheets.main import fetch_student_record
from engine.handle import Handle
from engine.messenger import Messenger
from tabulate import tabulate


def generate(student_id: str, messenger: Messenger) -> None:

    remote = CachedSheetPlugin(
        repo_url='https://github.com/shomilj/ag-frontend-demo-csv-sync',
        sheet_url='https://docs.google.com/spreadsheets/d/1RPpWVcu_jB3unDzf3oWVM7jbHb4fgyBr8hkEAJNuQY0/edit#gid=893408305',
        google_service_account='service-account.json'
    )

    if student_id == "SYNC":
        remote.sync()
        messenger.log("Successfully performed sync.")
    else:
        record = remote.get_student_record(
            sheet_name='Roster',
            sid_col='Student ID',
            sid=student_id
        )

        table = [['Exam Start Date', record['Start Day']],
                 ['Exam Start Time', record['Start Time']],
                 ['Exam End Time', record['End Time']],
                 ['Format', record['Format']],
                 ['Accommodations', record['Accommodations']]]

        messenger.log(tabulate(table, tablefmt="fancy_grid"), section='Exam Information')

        if record['Notes'] != '':
            messenger.log(record['Notes'], section='Additional Notes')


if __name__ == "__main__":
    Handle.run(generate=generate, root='test-root/')
