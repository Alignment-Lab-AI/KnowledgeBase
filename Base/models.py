import datetime
import duckdb
import sqlite3
import os
from Base.period import Period

def initialize(fname):
    os.makedirs('data', exist_ok=True)
    sqlite_file = os.path.join('data', fname)
    con = sqlite3.connect(sqlite_file)
    con.execute("""
        CREATE TABLE IF NOT EXISTS process (
            id INTEGER PRIMARY KEY,
            name VARCHAR UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS window (
            id INTEGER PRIMARY KEY,
            title VARCHAR,
            process_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (process_id) REFERENCES process(id)
        );
        
        CREATE TABLE IF NOT EXISTS geometry (
            id INTEGER PRIMARY KEY,
            xpos INTEGER NOT NULL,
            ypos INTEGER NOT NULL,
            width INTEGER NOT NULL, 
            height INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS click (
            id INTEGER PRIMARY KEY,
            button INTEGER NOT NULL,
            press BOOLEAN NOT NULL,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            nrmoves INTEGER NOT NULL,
            process_id INTEGER NOT NULL,
            window_id INTEGER NOT NULL,
            geometry_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (process_id) REFERENCES process(id),
            FOREIGN KEY (window_id) REFERENCES window(id),
            FOREIGN KEY (geometry_id) REFERENCES geometry(id)
        );
        
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY,
            text VARCHAR NOT NULL,
            started TIMESTAMP NOT NULL,
            process_id INTEGER NOT NULL,
            window_id INTEGER NOT NULL,
            geometry_id INTEGER NOT NULL,
            nrkeys INTEGER,
            keys VARCHAR,
            timings VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (process_id) REFERENCES process(id),
            FOREIGN KEY (window_id) REFERENCES window(id),
            FOREIGN KEY (geometry_id) REFERENCES geometry(id)
        );

        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY,
            process_id INTEGER NOT NULL,
            window_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (process_id) REFERENCES process(id),
            FOREIGN KEY (window_id) REFERENCES window(id)
        );

        CREATE TABLE IF NOT EXISTS screenshot (
            id INTEGER PRIMARY KEY,
            process_id INTEGER NOT NULL,
            window_id INTEGER NOT NULL,
            geometry_id INTEGER NOT NULL,
            image BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (process_id) REFERENCES process(id),
            FOREIGN KEY (window_id) REFERENCES window(id),
            FOREIGN KEY (geometry_id) REFERENCES geometry(id)
        );

        CREATE INDEX IF NOT EXISTS idx_click_created_at ON click (created_at);
        CREATE INDEX IF NOT EXISTS idx_keys_created_at ON keys (created_at);
        CREATE INDEX IF NOT EXISTS idx_activity_start_time ON activity (start_time);
        CREATE INDEX IF NOT EXISTS idx_activity_end_time ON activity (end_time);
        CREATE INDEX IF NOT EXISTS idx_screenshot_created_at ON screenshot (created_at);
    """)
    return con

def export_to_parquet(sqlite_file):
    parquet_file = sqlite_file.replace('.db', '_' + datetime.datetime.now().strftime('%m-%d-%y') + '.parquet')
    duckdb_con = duckdb.connect()
    duckdb_con.execute(f"INSTALL sqlite;")
    duckdb_con.execute(f"LOAD sqlite;")
    duckdb_con.execute(f"ATTACH DATABASE '{sqlite_file}' AS sqlite;")
    for table_name in ['process', 'window', 'geometry', 'click', 'keys', 'activity', 'screenshot']:
        duckdb_con.execute(f"""
            COPY (SELECT * FROM sqlite.{table_name}) TO '{parquet_file}_{table_name}.parquet' (FORMAT 'parquet');
        """)

class Process:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<Process '{self.name}'>"

class Window:
    def __init__(self, title, process_id):
        self.title = title
        self.process_id = process_id

    def __repr__(self):
        return f"<Window '{self.title}'>"

class Geometry:
    def __init__(self, x, y, width, height):
        self.xpos = x
        self.ypos = y
        self.width = width
        self.height = height

    def __repr__(self):
        return f"<Geometry ({self.xpos}, {self.ypos}), ({self.width}, {self.height})>"

class Click:
    def __init__(self, button, press, x, y, nrmoves, process_id, window_id, geometry_id):
        self.button = button
        self.press = press
        self.x = x
        self.y = y
        self.nrmoves = nrmoves
        self.process_id = process_id
        self.window_id = window_id
        self.geometry_id = geometry_id

    def __repr__(self):
        return f"<Click ({self.x}, {self.y}), ({self.button}, {self.press}, {self.nrmoves})>"

class Keys:
    def __init__(self, text, keys, timings, nrkeys, started, process_id, window_id, geometry_id):
        self.text = text
        self.keys = keys
        self.timings = timings
        self.nrkeys = nrkeys
        self.started = started
        self.process_id = process_id
        self.window_id = window_id
        self.geometry_id = geometry_id

    def __repr__(self):
        return f"<Keys {self.nrkeys}>"

class Activity:
    def __init__(self, process_id, window_id, start_time, end_time):
        self.process_id = process_id
        self.window_id = window_id
        self.start_time = start_time
        self.end_time = end_time

    def duration(self):
        return self.end_time - self.start_time

    @staticmethod
    def get_for_process(process_id, start_time, end_time, sqlite_file):
        duckdb_con = duckdb.connect()
        duckdb_con.execute("INSTALL sqlite;")
        duckdb_con.execute("LOAD sqlite;")
        duckdb_con.execute(f"ATTACH DATABASE '{sqlite_file}' AS sqlite;")
        
        parquet_files = [f for f in os.listdir('data') if f.endswith('.parquet')]
        for parquet_file in parquet_files:
            duckdb_con.execute(f"""
                CREATE VIEW IF NOT EXISTS {parquet_file} AS 
                SELECT * FROM parquet_scan('data/{parquet_file}') 
            """)
        
        periods = Period(datetime.timedelta(seconds=5), end_time)
        rows = duckdb_con.execute("""
            SELECT process_id, window_id, start_time, end_time 
            FROM sqlite.activity
            UNION ALL BY NAME
            SELECT process_id, window_id, start_time, end_time
            FROM activity
            WHERE process_id = ? AND start_time >= ? AND start_time <= ?
            ORDER BY start_time
        """, [process_id, start_time, end_time])
        periods.extend(row[2] for row in rows.fetchall())
        return periods.times

    def __repr__(self):
        return f"<Activity process:{self.process_id} window:{self.window_id} duration:{self.duration()}>"

class Screenshot:
    def __init__(self, process_id, window_id, geometry_id, image):
        self.process_id = process_id
        self.window_id = window_id
        self.geometry_id = geometry_id
        self.image = image

    def __repr__(self):
        return f"<Screenshot process:{self.process_id} window:{self.window_id}>"