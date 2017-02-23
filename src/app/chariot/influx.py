from influxdb import InfluxDBClient

host = 'influx'
port = 8086
user = 'root'
password = 'root'
database = 'chariot'

influx = InfluxDBClient(host, port, user, password, database)
influx.create_database(database)


def select(func):
    return InfluxSelect("SELECT " + func + "(value)")


def select_from(table):
    return InfluxTable("SELECT value FROM " + table)


def drop_from(table):
    return InfluxTable("DROP SERIES FROM " + table)


class InfluxBase:
    query = ""

    def __init__(self, query):
        self.query = query


class InfluxSelect(InfluxBase):
    def from_table(self, table):
        return InfluxTable(self.query + " FROM " + table)

    def select(self, func):
        return InfluxSelect(self.query + ", " + func + "(value)")


class InfluxFetchable(InfluxBase):
    def execute(self):
        return influx.query(query=self.query)

    def fetch(self):
        return list(influx.query(query=self.query, epoch='ms').get_points())

    def fetch_one(self):
        result = self.fetch()
        if result and len(result) > 0:
            return result[0]
        return None


class InfluxTable(InfluxFetchable):
    def where(self, var):
        return InfluxConditional(self.query + " WHERE " + var)


class InfluxConditional(InfluxBase):
    def eq(self, value):
        return InfluxCondition(self.query + "='" + str(value) + "'")

    def gt(self, value):
        return InfluxCondition(self.query + ">'" + str(value) + "'")

    def gte(self, value):
        return InfluxCondition(self.query + ">='" + str(value) + "'")

    def lt(self, value):
        return InfluxCondition(self.query + "<'" + str(value) + "'")

    def lte(self, value):
        return InfluxCondition(self.query + "<='" + str(value) + "'")


class InfluxCondition(InfluxFetchable):
    def where(self, var):
        return InfluxConditional(self.query + " AND " + var)
