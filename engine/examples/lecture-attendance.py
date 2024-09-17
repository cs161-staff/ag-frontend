from engine.extensions.sheets.main import fetch_student_record
from engine.handle import Handle
from engine.messenger import Messenger
from tabulate import tabulate

# For documentation on how to use this template, see
# https://docs.google.com/document/d/1Qi6SXin7vmHRc62UWIgUSd00r6ADiEaWo6Nki8Pf7Pg

def generate(student_id: str, messenger: Messenger) -> None:

    # Look up room number & assignments using Google Sheets API
    # Remember to change spreadsheet URL!
    record = fetch_student_record(
        student_id=student_id,
        spreadsheet_url="https://docs.google.com/spreadsheets/d/1GGeuaJKEcjlB1NFLxHyHvn5gr1dLk1XPkcfw-cEyIvw/edit?gid=364751914",
        worksheet_index=0,
        credentials_dir='/autograder/source/keys/google-service-accounts/'
    )

    # In each sublist, the first item is the name students see on the autograder,
    # and the second item is the column to pull from Gradescope.
    #
    # Example: ['Total Attendance', record['Total']]
    # Student sees 'Total Attendance' on the autograder.
    # We pull a cell from the 'Total' column and the student's row (row lookup by SID).
    rows = [['Total Attendance', record['Total']],
            ['Lecture 6 (Tue, Sep 17)', record['6']],
            ['Lecture 7 (Thu, Sep 19)', record['7']]]

    messenger.log(tabulate(rows, tablefmt="fancy_grid"), section='Lecture Attendance')


if __name__ == "__main__":
    Handle.run(generate=generate, root='test-root/')
