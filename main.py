import json
import argparse
from enum import Enum
import logging
import os
import sqlite3
import sys

logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class DataBaseHandler:
    def __init__(self, db_name):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()

    def create_events_table(self, table_name):
        self.cursor.execute("""
                CREATE TABLE {} (event_id integer, date text, time integer, user_id integer, user_name text)""".format(
            table_name))

    def create_failed_events_table(self, table_name):
        self.cursor.execute("""
            CREATE TABLE {} (event_id integer, errors text)""".format(table_name))

    def drop_table(self, table_name):
        self.cursor.execute("""DROP TABLE {}""".format(table_name))

    def insert_event(self, event, table_name='events'):
        rows = self.cursor.execute("""SELECT * FROM {}""".format(table_name))
        already_exists = False
        for row in rows:
            curr_id = row[0]
            if event.event_id_ == curr_id:
                already_exists = True
        if not already_exists:
            self.cursor.execute("""INSERT INTO {} VALUES (?, ?, ?, ?, ?)""".format(table_name),
                                (event.event_id_, event.date_, event.time_, event.user_id_, event.user_name_))

    def insert_failed_event(self, event, table_name='failed_events'):
        rows = self.cursor.execute("""SELECT * FROM {}""".format(table_name))
        already_exists = False
        for row in rows:
            curr_id = row[0]
            if event.event_id_ == curr_id:
                already_exists = True
        if not already_exists:
            self.cursor.execute("""INSERT INTO {} VALUES (?, ?)""".format(table_name),
                                (event.event_id_, "\n".join(event.errors)))

    def select_all(self, table_name):
        rows = self.cursor.execute("""SELECT * FROM {}""".format(table_name))
        print("======{}======".format(table_name))
        for row in rows:
            print(row)


class EventRow:
    def __init__(self, serialized_event):
        self.event_id_ = serialized_event['event_id']
        self.user_id_ = serialized_event['user_id']
        self.user_name_ = serialized_event['user_name']
        self.date_ = serialized_event['date']
        self.time_ = serialized_event['time']
        self.data_is_valid = True
        self.errors = []

    def fix_error_message(self, message_text):  # fix == write down, not correct (yet)
        logging.error(message_text)
        self.errors.append(message_text)
        self.data_is_valid = False

    def validate(self):
        if not self.event_id_:
            self.fix_error_message("FAIL. Event id cannot be null")

        if not isinstance(self.event_id_, int):
            self.fix_error_message("FAIL. Event id should be stored as int")

        if not isinstance(self.user_id_, int):
            self.fix_error_message("FAIL. User id should be stored as int")

        if not isinstance(self.user_name_, str):
            self.fix_error_message("FAIL. User id should be stored as string")

        if not isinstance(self.date_, str):
            self.fix_error_message("FAIL. Date should be stored as string")

        if not isinstance(self.time_, float):
            self.fix_error_message("FAIL. Time should be stored as float")

        if self.data_is_valid:
            logging.info("Validation went successful")
        else:
            logging.error("Event {} is not valid".format(self.event_id_))
        return self.data_is_valid

    def print(self):
        print("""
        event_id: {},
        user_id: {},
        user_name: {},
        date: {},
        time: {},
        """.format(self.event_id_, self.user_id_, self.user_name_, self.date_, self.time_))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser(
        description=(
            'Takes json with event content as an input and, validates it and loads to the database. '
            'Path to the database should be also specified.'
        )
    )

    argument_parser.add_argument(
        '--db-dir',
        action='store',
        dest='db_dir',
        required=True,
        help='path to the file of the database'
    )

    argument_parser.add_argument(
        '--json-file',
        action='store',
        dest='json_file',
        required=True,
        help='json file with events')

    argument_parser.add_argument(
        '--first-run',
        action='store_true',
        dest='first_run',
        required=False,
        help="Defines if it's the first run of the script"
    )
    arguments = argument_parser.parse_args()
    json_file = arguments.json_file
    db_dir = arguments.db_dir
    os.chdir(db_dir)
    with open(json_file) as f:
        events = json.load(f)
    db_handler = DataBaseHandler('events.db')
    if arguments.first_run:
        # db_handler.drop_table('events')
        # db_handler.drop_table('failed_events')
        db_handler.create_events_table('events')
        db_handler.create_failed_events_table('failed_events')
    for event in events:
        event = EventRow(event)
        if not event.validate():
            db_handler.insert_failed_event(event, 'failed_events')
        else:
            db_handler.insert_event(event, 'events')
    db_handler.select_all('events')
    db_handler.select_all('failed_events')
    db_handler.connection.commit()
    db_handler.connection.close()
