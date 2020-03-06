#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================
import re
import subprocess
from typing import List, Dict

TRACKED_TAGS = {"features": "NEW FEATURE", "bug": "BUG FIX"}


def get_commits_msgs(from_tag: str, to_tag: str) -> List[Dict[str, str]]:
    """get commit from [from_tag; to_tag]

    Parameters
    ----------
    from_tag : str
        older git tag to consider to build the release
    to_tag : str
        newer git tag to consider to build the release

    Return
    ------
    list
        list of dictionary representing commit contents, commits are
        sorted from the newer one to the older
    """
    commits = str(
        subprocess.check_output(["git", "log", f"{from_tag}..{to_tag}"],
                                universal_newlines=True))
    commits_list = re.split(r"commit [\S]{40}", commits)

    # first one contains nothing
    commits_list.pop(0)

    commit_list_dico = []
    for commit in commits_list:
        author = re.findall(r"Author: [\w ]* <[\w\W*]*>",
                            commit)[0].replace("Author: ", "")
        date = re.findall(r"Date:[ \w:]*", commit)[0].replace("Date:   ", "")
        content = list(filter(lambda x: x is not "", commit.split("\n")))[-1]
        commit_list_dico.append({
            "author": author,
            "date": date,
            "content": content
        })

    return commit_list_dico


def release_header(from_tag: str, to_tag: str) -> str:
    """
    """
    header = f"iota2-{to_tag} - Changes since version {from_tag}\n"
    header += "-" * len(header)
    header += "\n\n"
    return header


def write_release(release_file: str, from_tag: str, to_tag: str) -> None:
    """write iota2 release rst file

    """

    commits = get_commits_msgs(from_tag, to_tag)
    commits_new_features = list(
        filter(lambda x: TRACKED_TAGS["features"] in x["content"], commits))
    commits_bug_fix = list(
        filter(lambda x: TRACKED_TAGS["bug"] in x["content"], commits))

    release_content = ""

    header = release_header(from_tag, to_tag)
    release_content += header

    features_add_title = "Features added"
    release_content += features_add_title
    release_content += "\n"
    release_content += "*" * len(features_add_title)
    release_content += "\n\n"

    for commit_new_feature in commits_new_features:
        new_feature = commit_new_feature["content"].replace(
            TRACKED_TAGS["features"] + " :", "")
        release_content += f"* {new_feature}\n"
    release_content += "\n\n"

    bugs_fixed_title = "Bugs fixed"
    release_content += bugs_fixed_title
    release_content += "\n"
    release_content += "*" * len(bugs_fixed_title)
    release_content += "\n\n"
    for commit_bug_fix in commits_bug_fix:
        print(commit_bug_fix["content"])
        bug_fixed = commit_bug_fix["content"].replace(
            TRACKED_TAGS["bug"] + " :", "")
        release_content += f"* {bug_fixed}\n"

    with open(release_file, "a") as r_notes:
        r_notes.write(release_content)


release_file = "/home/uz/vincenta/tmp/RELEASE_NOTES.rst"
write_release(release_file, "v0.5.1", "v0.5.2")
