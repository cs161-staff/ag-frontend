"""
This module provides a better approach to sync data from Google Sheets that uses GitHub as a caching
layer to avoid dealing with rate limiting issues.

Setup Instructions:
--------------------------------
[A] GITHUB SETUP:

1) Create a SSH Keypair. On Mac, you may do so by running "ssh-keygen -t rsa"
2) Upload the SSH Public Key to GitHub
3) Put the SSH Private Key into the "/keys/github/deploy_key" file in this repository.
   Note that the entire "keys" directory is excluded from version control.
4) Create a new PRIVATE GitHub repository in your organization's repository.
--------------------------------
[B] GOOGLE SETUP

1) Setup a Google Service Account using the steps outlined in the "For Bots: Using Service Account"
   section of the Gspread docs: https://docs.gspread.org/en/latest/oauth2.html
2) Copy the JSON file to /keys/google-service-accounts/
3) Add the client_email from the JSON file to your Google Sheet with view access.
--------------------------------
[C] USING THIS LIBRARY

1) Use the fetch_student_record(...) method to fetch a record. Alternatively, use the
   fetch_table(...) method to fetch an entire table.
--------------------------------
[D] DAILY UPDATES:

1) Re-run the autograder on a dummy student with `id.txt` file set to FORCE_REFRESH. This will
   trigger a fetch-and-sync procedure, where we copy the Sheet into the GitHub repo.

2) Re-run the autograder on all students. 
"""

import csv
import os.path
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

import gspread

from engine.error import VisibleError

# BASE_DIR = '/autograder/engine/extensions/cached_sheets/'
BASE_DIR = 'engine/extensions/cached_sheets/'

SCOPES = ['https://spreadsheets.google.com/feeds',
          'https://www.googleapis.com/auth/drive']


class CachedSheetPlugin():

    def __init__(self, repo_url: str, sheet_url: str, encryption_key: Optional[str] = None,
                 google_service_account: str = 'service-account.json') -> None:
        self.repo_url = repo_url
        self.repo_name = repo_url.split('/')[-1].replace('.git', '').strip()
        self.sheet_url = sheet_url
        self.encryption_key = encryption_key
        self.google_service_account = f'keys/google-service-accounts/{google_service_account}'

        if encryption_key:
            raise NotImplementedError("This feature is not implemented yet.")

    @property
    def _repo_dir(self) -> str:
        return os.path.join(BASE_DIR, self.repo_name)

    @property
    def _git_flags(self) -> Tuple[str, ...]:
        return f'--work-tree={self._repo_dir}', f"--git-dir={os.path.join(self._repo_dir, '.git')}"

    def pull_repo(self):
        if os.path.exists(os.path.join(self._repo_dir, '.git')):
            subprocess.run(('git', *self._git_flags, 'fetch'), check=True)
            subprocess.run(('git', *self._git_flags, 'checkout', '-f', 'origin/master'), check=True)
            subprocess.run(('git', *self._git_flags, 'clean', '-dfx'), check=True)
        else:
            shutil.rmtree(self._repo_dir, ignore_errors=True)
            subprocess.run(('git', 'clone', self.repo_url, self._repo_dir), check=True)
            subprocess.run(('git', *self._git_flags, 'checkout', '-f', 'origin/master'), check=True)

    def push_repo(self):
        subprocess.run(('git', *self._git_flags, 'add', '-A'), check=True)
        subprocess.run(('git', *self._git_flags, 'commit', '-m', 'sync'), check=True)
        subprocess.run(('git', *self._git_flags, 'push'), check=True)

    def read_sheet(self, sheet_name: str) -> List[Dict[str, Any]]:
        self.pull_repo()
        with open(BASE_DIR + self.repo_name + '/' + sheet_name + '.csv') as file:
            reader = csv.DictReader(file)
            return list(reader)

    def get_student_record(self, sheet_name: str, sid: str, sid_col: str = "Student ID") -> Dict[str, Any]:
        sheet = self.read_sheet(sheet_name=sheet_name)
        for row in sheet:
            if row.get(sid_col) == sid:
                return row
        raise VisibleError("Invalid student ID.")

    def sync(self):
        """
        Clone repository
        Download contents of spreadsheet using gspread
        Push repository
        """
        self.pull_repo()
        gc = gspread.service_account(
            self.google_service_account, scopes=SCOPES)
        ss = gc.open_by_url(self.sheet_url)
        for ws in ss.worksheets():
            filename = BASE_DIR + self.repo_name + '/' + ws.title + '.csv'
            with open(filename, 'w') as file:
                writer = csv.writer(file)
                writer.writerows(ws.get_all_values())
        self.push_repo()
