from typing import Dict, List, Optional


class Messenger:

    def __init__(self) -> None:
        self._output: List[str] = []
        self._tests: Dict[str, List[str]] = {}
        self.debug = False

    def log(self, message: str = '', section: Optional[str] = None) -> None:
        if section:
            self._tests[section] = self._tests.get(section, []) + [message]
        else:
            self._output.append(message)

    def reset(self) -> None:
        self._output = []
        self._tests = {}

    def _to_gradescope(self) -> Dict:
        output = '\n'.join(self._output)
        tests = [{
            "name": title,
            "output": '\n'.join(messages)
        } for title, messages in self._tests.items()]

        if self.debug:
            print('*'*30)
            print(output)
            for row in tests:
                print('-'*10)
                print(row.get('name'))
                print(row.get('output'))

        return {
            "score": 1,
            "visibility": "after_published",
            "stdout_visibility": "after_published",
            "output": output,
            "tests": tests
        }
