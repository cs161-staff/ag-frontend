from engine.utils.sheets import fetch_student_record
from engine.handle import Handle
from engine.messenger import Messenger
from tabulate import tabulate


def generate(student_id: str, messenger: Messenger) -> None:

    # Look up room number & assignments using Google Sheets API
    record = fetch_student_record(
        credentials_dir='keys/',
        student_id=student_id,
        spreadsheet_url="https://docs.google.com/spreadsheets/d/1tJjglHchD7gVfGGgCeG8KRcNnHV-GbvibHP3MlxCXQc/edit#gid=0",
        worksheet_index=0
    )

    rows = [['Row Number', record['Row']],
            ['Seat Number', record['Seat']],
            ['Exam Room', record['Room']]]

    messenger.log(tabulate(rows, tablefmt="fancy_grid"), section='Room Assignments')


if __name__ == "__main__":
    Handle.run(generate=generate, root='test-root/')
