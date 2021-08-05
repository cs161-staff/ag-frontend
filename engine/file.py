from typing import Any, Dict, Optional
from engine.error import VisibleError
import json

FILE_ERR = "An error occurred while parsing your student ID file."

import os

class FileManager:

    @staticmethod
    def is_live():
        return os.path.exists('/autograder')

    @staticmethod
    def read_student_id() -> str:
        try:
            with open('/autograder/submission/id.txt') as file:
                student_id = file.read().strip()
                return student_id

        except Exception:
            raise VisibleError(FILE_ERR)

    @staticmethod
    def write_output(output: Dict[str, Any]) -> None:
        if FileManager.is_live():
            with open('/autograder/results/results.json', 'w') as file:
                json.dump(output, file)