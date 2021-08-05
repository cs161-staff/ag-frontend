from engine.handle import Handle
from engine.messenger import Messenger


def generate(student_id: str, messenger: Messenger) -> None:
    """
    TODO: Fill this out with whatever you'd like!
    """
    messenger.log(f'Hello world - student {student_id}!')


if __name__ == "__main__":
    Handle.run(generate=generate, root='test-root/')
