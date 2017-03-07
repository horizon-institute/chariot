import re
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
    def list(self):
        return list(influx.query(self.query, epoch='ms').get_points())

    def first(self):
        results = self.list()
        if results and len(results) > 0:
            return results[0]
        return None

    def fetch(self):
        return InfluxResponse(query=self.query, data=self.list())


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

    def limit(self, limit):
        return InfluxFetchable(self.query + " LIMIT " + str(limit))


class InfluxResponse(InfluxBase):
    offset = 0
    limit = 10000
    data = []

    def __init__(self, query, data, offset = 0):
        InfluxBase.__init__(self, query)
        self.data = data
        self.offset = offset
        match = re.search(' LIMIT (\d+)', query)
        if match:
            self.limit = int(match.group(1))

    def is_partial(self):
        return len(self.data) == self.limit

    def list(self):
        return self.data

    def first(self):
        if self.data and len(self.data) > 0:
            return self.data[0]
        return None

    def next(self):
        new_offset = self.offset + self.limit
        offset_query = InfluxFetchable(self.query + " OFFSET " + str(new_offset))
        response = offset_query.fetch()
        response.offset = new_offset
        response.query = self.query
        return response
