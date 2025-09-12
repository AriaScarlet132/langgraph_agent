from app.utils.data import get_token, get_table_definition, query_data

if __name__ == "__main__":
    host = "http://192.168.10.21:3000"
    # print(get_token("http://192.168.10.21:3000"))
    token = get_token(host)
    # print(get_table_definition(host, token, "Admin", "ServiceOrderInfoQueryDS_Datav"))
    print(query_data(host, token, "Admin", "SELECT count(*) FROM ServiceOrderInfoQueryDS_Datav", "ServiceOrderInfoQueryDS_Datav"))