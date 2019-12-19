import sqlite3


def iterate_collection_as_tuples(collection):
    for item in collection:
        yield (item,)


class SqliteDataHandler:
    staged_passwords = "staged"
    working_passwords = "working"
    omissions = "omissions"
    derivatives = "derivatives"

    def __init__(self):
        self.db = sqlite3.connect("")
        self.db.execute("create table ? (password text, unique(password))", (self.staged_passwords,))
        self.db.execute("create table ? (password text, unique(password))", (self.working_passwords,))
        self.db.execute("create table ? (password text, unique(password))", (self.omissions,))
        self.db.execute("create table ? (password text, unique(password))", (self.derivatives,))
        self.db.commit()

    def commit(self):
        self.db.commit()

    def password_is_omitted(self, password):
        cursor = self.db.execute("select * from ? where password = ?", (self.omissions, password))
        if cursor.rowcount > 0:
            return False
        return True

    def stage_password(self, password, auto_commit=True):
        self.db.execute("insert or ignore into ? values (?)", (self.staged_passwords, password))
        if auto_commit:
            self.db.commit()

    def stage_many_passwords(self, collection, auto_commit=True):
        statement = "insert or ignore into %s values(?)" % self.staged_passwords
        self.db.executemany(statement, iterate_collection_as_tuples(collection))
        if auto_commit:
            self.db.commit()

    def flush_staged_passwords(self, auto_commit=True):
        self.db.execute("insert or ignore into ?(password) select password from ?", (self.derivatives, self.staged_passwords))
        self.db.execute("insert or ignore into ?(password) select password from ?", (self.working_passwords, self.staged_passwords))
        self.db.execute("delete from ?", (self.staged_passwords,))
        if auto_commit:
            self.db.commit()

    def working_password_count(self):
        return self.db.execute("select count(password) from ?", (self.working_passwords,)).fetchone()[0]

    def get_working_password_iterator(self):
        cursor = self.db.execute("select password from ?", (self.working_passwords,))
        return cursor

    def get_derivative_iterator(self):
        cursor = self.db.execute("select password from ?", (self.derivatives,))
        return cursor

    def close(self):
        self.db.close()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

