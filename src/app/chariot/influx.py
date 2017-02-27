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
        params = {
            'q': self.query,
            'db': database,
            'epoch': 'ms'

        }
        response = influx.request(
            url="query",
            method='GET',
            params=params,
            data=None,
            expected_response_code=200
        )

        response_json = response.json()
        results = response_json.get('results', [{}])[0]
        series = results.get('series', [{}])[0]

        return InfluxResponse(query=self.query, response=series)


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

    def offset(self, offset):
        return InfluxCondition(self.query + " OFFSET " + str(offset))


class InfluxResponse(InfluxBase):
    response = ""
    offset = 0
    limit = 10000

    def __init__(self, query, response, offset=0):
        InfluxBase.__init__(self, query)
        self.response = response
        self.offset = offset

    def is_partial(self):
        return self.response.get('partial', False)

    def list(self):
        data = []
        columns = self.response.get('columns', [])
        for value in self.response.get('values', []):
            point = {}
            for col_index, col_name in enumerate(columns):
                point[col_name] = value[col_index]
            data.append(point)

        return data

    def first(self):
        result = self.list()
        if result and len(result) > 0:
            return result[0]
        return None

    def next(self):
        offset_query = InfluxFetchable(self.query + "LIMIT " + str(self.limit) + " OFFSET " + str(self.offset + self.limit))
        response = offset_query.fetch()
        response.offset = self.offset + self.limit
        response.query = self.query
        return response
