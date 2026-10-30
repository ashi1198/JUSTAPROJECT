"""Saving and loading crawl results.

This file only uses the standard library. It must NOT import main.py:
main.py imports this file, so importing back would be a circular import.
"""

import json

from dataclasses import asdict


def records_to_dicts(records):
    list_dict = []
    for record in records:
        record_dict = asdict(record)
        list_dict.append(record_dict)
    return list_dict


def save_results(records, summary, path):

    result_dict = dict()
    result_dict["summary"] = summary
    list_dict = records_to_dicts(records)
    result_dict["pages"] = list_dict
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)


def load_results(path):

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["summary"], data["pages"]


# ---------------------------------------------------------------------------
# OPTIONAL (only if you have time): SQLite storage using the sqlite3 module
# ---------------------------------------------------------------------------
def save_sqlite(records, path):
    """Store the records in a SQLite database file.

    TODO (optional):
      1. import sqlite3 and connect to `path`
      2. CREATE TABLE IF NOT EXISTS pages(url TEXT, depth INTEGER, status INTEGER,
         error TEXT, attempts INTEGER, title TEXT, link_counts TEXT)
      3. insert one row per record (store link_counts with json.dumps)
      4. commit and close the connection
    """
    raise NotImplementedError
