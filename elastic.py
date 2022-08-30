from elasticsearch import Elasticsearch


class Elastic:

    def __init__(self, index_name):
        self.es = Elasticsearch(hosts=['http://127.0.0.1:9200'])
        self.index_name = index_name

    def index(self, body, id):
        self.es.index(index=self.index_name,
                      body=body,
                      id=id)

    def update(self, body, id):
        self.es.update(index=self.index_name,
                       body=body,
                       id=id)

    def get_nft_by_id(self, id):
        return self.es.get(index=self.index_name, id=id)

    def get_recently_updated(self, custom_size=69,
                             custom_from=0,
                             user_query=None,
                             file_types=None):
        filter_array = [{
            "range" : {
                "files_count.t" : { "gte" : 1}
            }
        }]
        body = self.__create_body(filter_array, custom_size, custom_from, user_query, file_types)
        return self.es.search(index=self.index_name, body=body)

    def get_recently_updated_free(self, custom_size=69,
                                  custom_from=0,
                                  user_query=None,
                                  file_types=None):
        filter_array = [
            {"range" : {
                "files_count.t" : { "gte" : 1}
            }},
            {"range" : {
                "price" : { "lte": 0, "gte" : 0}
            }}
        ]
        body = self.__create_body(filter_array, custom_size, custom_from, user_query, file_types)
        return self.es.search(index=self.index_name, body=body)

    def get_recently_updated_top(self, custom_size=69,
                                 custom_from=0,
                                 user_query=None,
                                 file_types=None):
        filter_array = [
            {"range" : {
                "files_count.t" : { "gte" : 1}
            }},
            {"range" : {
                "average_quality" : { "gte" : 4}
            }},
            {"range" : {
                "quality_count" : { "gte" : 3}
            }},
            {"range" : {
                "total_count" : { "gte" : 3}
            }},
            {"range" : {
                "genuine_percent" : { "gte" : 70}
            }}
        ]
        body = self.__create_body(filter_array, custom_size, custom_from, user_query, file_types)
        return self.es.search(index=self.index_name, body=body)

    def get_recently_updated_with_preview(self, custom_size=69,
                                 custom_from=0,
                                 user_query=None,
                                 file_types=None):
        filter_array = [
            {"range" : {
                "files_count.t" : { "gte" : 1}
            }},
            {"range" : {
                "preview_files_count" : { "gte" : 1}
            }}
        ]
        body = self.__create_body(filter_array, custom_size, custom_from, user_query, file_types)
        return self.es.search(index=self.index_name, body=body)

    def get_user_nfts(self, user, custom_size=69, custom_from=0):
        body = {
            "query": {
                "bool": {
                    "must": {
                        "match_all": {}
                    },
                    "filter": {
                        "term": {
                            "owner": {
                                "value": user
                            }
                        }
                    }
                }
            },
            "sort" : [
                { "creation_time": {"order" : "desc"}}
            ],
            "size": custom_size,
            "from": custom_from*custom_size
        }
        return self.es.search(index=self.index_name,
                              body=body)

    def get_purchased_nfts(self, ids, custom_size=69):
        body = {
            "query": {
                "ids" : {
                    "values" : ids
                }
            },
            "sort" : [
                { "update_time": {"order" : "desc"}}
            ],
            "size": custom_size
        }
        return self.es.search(index=self.index_name,
                              body=body)

    @staticmethod
    def __create_file_types_query(file_types):
        types_array = []
        if file_types is not None:
            if 'v' in file_types:
                types_array.append(
                    {"range" : {
                        "files_count.v" : { "gte" : 1}
                    }})
            if 'p' in file_types:
                types_array.append(
                    {"range" : {
                        "files_count.p" : { "gte" : 1}
                    }})
            if 'd' in file_types:
                types_array.append(
                    {"range" : {
                        "files_count.d" : { "gte" : 1}
                    }})
            if 'a' in file_types:
                types_array.append(
                    {"range" : {
                        "files_count.a" : { "gte" : 1}
                    }})
            if 'o' in file_types:
                types_array.append(
                    {"range" : {
                        "files_count.o" : { "gte" : 1}
                    }})
        if len(types_array) == 0:
            types_array.append({ "match_all": {} })
        return types_array

    @staticmethod
    def __create_match_query(user_query):
        if user_query is None:
            match = { "match_all": {} }
        else:
            match = [
                {
                    "match" : {
                        "name" : {
                            "query" : user_query,
                            "operator" : "and",
                            "fuzziness": "AUTO",
                            "zero_terms_query": "all"
                        }
                    }
                },
                {
                    "match" : {
                        "description" : {
                            "query" : user_query,
                            "operator" : "and",
                            "fuzziness": "AUTO",
                            "zero_terms_query": "all"
                        }
                    }
                },
                {
                    "match" : {
                        "files" : {
                            "query" : user_query,
                            "operator" : "and",
                            "fuzziness": "AUTO",
                            "zero_terms_query": "all"
                        }
                    }
                }
            ]
        return match

    def __create_body(self, filter_array, custom_size, custom_from, user_query, file_types):
        types_array = self.__create_file_types_query(file_types)
        only_active_filter = {
            "term": {
                "status": {
                    "value": "ACTIVE"
                }
            }
        }
        filter_array.append(only_active_filter)
        return {
            "query": {
                "bool": {
                    "must" : {
                        "bool" : {
                            "should" : self.__create_match_query(user_query)
                        }
                    },
                    "should": types_array,
                    "filter": filter_array,
                    "minimum_should_match": 1
                }
            },
            "sort" : [
                { "update_time": {"order" : "desc"}}
            ],
            "size": custom_size,
            "from": custom_from*custom_size
        }

    def search_nfts(self, query):
        body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"name": query}},
                        {"match": {"description": query}},
                        {"match": {"files": query}},
                        {"match": {"preview_files": query}}
                    ],
                    "filter": [
                        #
                        #{"term": {"status": "ACTIVE"}},
                        #{ "range": { "publish_date": { "gte": "2015-01-01" }}}
                    ]
                }
            }
        }
        return self.es.search(index=self.index_name,
                       body=body)

    def test(self, id):
        test_dic = {}
        test_dic['name'] = 'blah blah blah'
        test_dic['time'] = '2019-09-03T13:54:02.305Z'
        self.es.index(index=self.index_name,
                      doc_type='_doc',
                      body=test_dic,
                      id=id)
