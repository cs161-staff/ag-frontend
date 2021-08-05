from engine.messenger import Messenger
from typing import Callable, Optional
from engine.file import FileManager
from engine.error import InternalError, VisibleError

TEST_STUDENT_ID = 123456

class Handle:

    @staticmethod
    def run(generate: Callable[[str, Messenger], None], root: Optional[str] = None):

        messenger = Messenger()
        messenger.debug = not FileManager.is_live()

        try:
            if FileManager.is_live():
                student_id = FileManager.read_student_id()
            else:
                student_id = TEST_STUDENT_ID
            generate(student_id, messenger)

        except InternalError as err:
            print('Internal Error: ', err)
            messenger.reset()
            messenger.log(
                'An internal error occurred. Please contact course staff.')

        except VisibleError as err:
            print('Visible Error: ', err)
            messenger.reset()
            messenger.log('An error occurred. Details:' + '\n\n' + str(err))

        FileManager.write_output(output=messenger._to_gradescope())
