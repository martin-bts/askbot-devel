import psycopg2

class DevDB(object):

    def __init__(self, username='askbot', password='askB0T!'):
        self.querys = []
        self.username = username
        self.password = password

    def _prepare(self, username, password):
        q = self.querys
        q.append("CREATE USER {username} WITH PASSWORD '{password}';")
        q.append("ALTER USER  {username} CREATEDB;")
        q.append("ALTER ROLE  {username} SET  client_encoding TO 'utf8';")
        q.append("ALTER ROLE  {username} SET  default_transaction_isolation TO 'read committed';")
        q.append("ALTER ROLE  {username} SET  timezone TO 'UTC';")
        q.append("ALTER USER  {username} CREATEDB;")

    def update_credentials(self, username=None, password=None):
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password

    def deploy(self, db_conn):
        db_conn.set_session('SERIALIZABLE')
        self._prepare(self.username, self.password)
        with db_conn.cursor() as c:
            for q in self.querys:
                c.execture(q)
            db_conn.commit()
            return
        db_conn.rollback()

if __name__ == "__main__":
    dsn = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=askbotPW"
    db_conn = psycopg2.connect(dsn)
    DevDB().deploy(db_conn)
    db_conn.close()

