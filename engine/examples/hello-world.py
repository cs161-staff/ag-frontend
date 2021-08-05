from engine.utils.sheets import fetch_student_record
from engine.handle import Handle
from engine.messenger import Messenger
from tabulate import tabulate


def generate(student_id: str, messenger: Messenger) -> None:
    messenger.log(f'Hello student {student_id}!')


if __name__ == "__main__":
    Handle.run(generate=generate, root='test-root/')
