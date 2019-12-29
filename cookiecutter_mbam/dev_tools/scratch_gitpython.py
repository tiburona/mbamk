#!/usr/bin/env python

import git
import sys
from pathlib2 import Path
from difflib import context_diff
from . import push_config


repo_path = Path(__file__).resolve().parents[1] # return the MBAM .git directory

repo = git.Repo(str(repo_path))

remote_name, remote_url = sys.argv[1:]

local_ref, local_sha1, remote_ref, remote_sha1 = [line for line in sys.stdin][0].split(' ')

if 'build-qa' in repo.head.commit.message:
    pass

# If we're not pushing to development there's nothing more to do.
if repo.active_branch.name != 'docs-and-config':
    sys.exit(0)

for i, commit in enumerate(repo.iter_commits('docs-and-config')):
    if commit.hexsha.strip() == remote_sha1.strip():
        remote_commit = commit
        break

sync_ps = sync_sem = sync_cfn = False

diff_names = repo.git.diff(remote_commit.hexsha, repo.active_branch.commit.hexsha)

if '/build/cfn/' in diff_names:
    sync_cfn = True

if 'config.yml' in diff_names:
    for diff_item in remote_commit.diff(repo.active_branch.commit).iter_change_type('M'):
        if 'config.yml' in str(diff_item):
            a_blob = diff_item.a_blob.data_stream.read().decode('utf-8').splitlines(keepends=True)
            b_blob = diff_item.b_blob.data_stream.read().decode('utf-8').splitlines(keepends=True)
            diff = context_diff(a_blob, b_blob, n=100)
            for line in diff:
                for section in ['TEST:', 'STAGING:', 'DOCKER:', 'TRUSTED:', 'LOCAL:']:
                    if section in line:
                        curr_section = section
                if line[0] == '!':
                    if curr_section in ['TEST:']:
                        sync_sem = True
                    if curr_section in ['STAGING:', 'DOCKER:', 'TRUSTED:']:
                        sync_ps = True


print("sync_cfn is {}\nsync_sem is {}\n, sync_ps is {}".format(sync_cfn, sync_sem, sync_ps))

remote_locations = {
   "the AWS parameter store": sync_ps,
   "Semaphore": sync_sem,
   "Cloudformation templates": sync_cfn
}

syncs = [k for k, v in remote_locations if v]

if len(syncs) < 3:
    sync_string = 'and '.join(syncs)
else:
    sync_string = ', '.join(syncs[:-1] + ', and' + syncs[-1])

cont = None

while cont not in ['Yes', 'no', 'Y', 'n', 'y']:

    cont = input("Your changes will be pushed to {}.  Do you want to continue? Yes/no.".format(sync_string))

    if cont not in ['Yes', 'no']:
        print('That is not a recognized value.')


if cont in ['Yes', 'Y', 'y']:
    push_config(sync_ps=sync_ps, sync_sem=sync_sem, sync_cfn=sync_cfn)
else:
    sys.exit("Sync aborted.")