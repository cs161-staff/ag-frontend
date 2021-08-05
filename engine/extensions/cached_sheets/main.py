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
import datetime
import os.path
import secrets
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

import gspread

from engine.error import VisibleError

# BASE_DIR = '/autograder/engine/extensions/cached_sheets/'
BASE_DIR = 'engine/extensions/cached_sheets/'

SCOPES = ['https://spreadsheets.google.com/feeds',
          'https://www.googleapis.com/auth/drive']

GIT_NAME = 'Gradescope Frontend'
GIT_EMAIL = 'cs161-staff@berkeley.edu'

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

    def _git(self, args, **kwargs) -> subprocess.CompletedProcess:
        # Default check=True.
        kwargs.setdefault('check', True)

        # Default git environment variables in env dict.
        kwargs['env'] = dict({
            'GIT_AUTHOR_NAME': GIT_NAME,
            'GIT_AUTHOR_EMAIL': GIT_EMAIL,
            'GIT_COMMITTER_NAME': GIT_NAME,
            'GIT_COMMITTER_EMAIL': GIT_EMAIL,
            'GIT_SSH_COMMAND': "ssh -o 'StrictHostKeyChecking no' -i keys/github/deploy_key",
        }, **kwargs.get('env', {}))

        git_flags = (f'--work-tree={self._repo_dir}', f"--git-dir={os.path.join(self._repo_dir, '.git')}")
        return subprocess.run(('git', *git_flags, *args), **kwargs)

    def pull_repo(self):
        if os.path.exists(os.path.join(self._repo_dir, '.git')):
            self._git(('fetch',))
            self._git(('checkout', '-f', 'origin/master'))
            self._git(('clean', '-dfx'))
        else:
            shutil.rmtree(self._repo_dir, ignore_errors=True)
            subprocess.run(('git', 'clone', self.repo_url, self._repo_dir))
            self._git(('checkout', '-f', 'origin/master'))

    def push_repo(self):
        self._git(('add', '-A'))
        self._git(('commit', '--allow-empty', '-m', 'sync'))
        self._git(('push', 'origin', 'HEAD:master'))

    def read_sheet(self, sheet_name: str) -> List[Dict[str, Any]]:
        self.sync()
        with open(BASE_DIR + self.repo_name + '/' + sheet_name + '.csv') as file:
            reader = csv.DictReader(file)
            return list(reader)

    def get_student_record(self, sheet_name: str, sid: str, sid_col: str = "Student ID") -> Dict[str, Any]:
        sheet = self.read_sheet(sheet_name=sheet_name)
        for row in sheet:
            if row.get(sid_col) == sid:
                return row
        raise VisibleError("Invalid student ID.")

    def _try_lock(self) -> bool:
        """Attempts to acquire the lock by pushing a new, dummy commit to a lock branch on the repo.
        If we succeed, we have the lock. If we fail, assume that someone else pushed to the lock
        branch and has the lock. The dummy commit contains a random hex string so that the commit
        IDs are guaranteed to be unique.

        Yes, this is janky.
        """
        self.pull_repo()
        now = datetime.datetime.utcnow()
        lock_name = f"lock-{now.strftime('%Y-%m-%d-%H%M')}"
        self._git(('checkout', '--orphan', lock_name))
        try:
            self._git(('reset',))
            self._git(('commit', '--allow-empty', '-m', f'{lock_name} {secrets.token_hex(16)}'))
            ret = self._git(('push', 'origin', lock_name), check=False)
            # The lock is acquired if the git push succeeded.
            return ret.returncode == 0
        finally:
            self._git(('checkout', '-f', 'origin/master'))
            self._git(('branch', '-D', lock_name))

    def sync(self):
        """Try acquiring the lock. If we succeed, update the repo cache from the spreadsheet using
        gspread. If we fail, someone else is updating the repo cache, and we repeatedly pull the
        repo until we receive a recent commit.
        """
        if self._try_lock():
            # Pull repo.
            self.pull_repo()

            # Download contents of spreadsheet using gspread.
            gc = gspread.service_account(
                self.google_service_account, scopes=SCOPES)
            ss = gc.open_by_url(self.sheet_url)
            for ws in ss.worksheets():
                filename = BASE_DIR + self.repo_name + '/' + ws.title + '.csv'
                with open(filename, 'w') as file:
                    writer = csv.writer(file)
                    writer.writerows(ws.get_all_values())

            # Push repo.
            self.push_repo()
        else:
            # Pull repo until we get a commit in the recent past.
            is_recent = False
            while not is_recent:
                self.pull_repo()
                ret = self._git(('show', '-s', '--format=%ct'), capture_output=True, text=True)
                commit_date = datetime.datetime.utcfromtimestamp(float(ret.stdout))
                print(datetime.datetime.utcnow(), commit_date)
                is_recent = datetime.datetime.utcnow() - commit_date < datetime.timedelta(minutes=5)
