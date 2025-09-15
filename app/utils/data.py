import requests

APP_ID = "agent"
APP_SECRET = "agent"

def get_token(host: str) -> str:
    response = requests.get(
        url=f"{host}/rest/oauth2/token",
        params={
            "grant_type": "client_credentials",
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
        }
    )
    if response.status_code == 200:
        return response.json().get("access_token", "")
    else:
        raise Exception(f"Failed to get token: {response.status_code}, {response.text}")

def get_table_definition(host: str, userid: str) -> str:
    token = get_token(host)
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(
        url=f"{host}/api/oauthaccess/datav/agent/queryDDL",
        headers=headers,
        json={
            "userid": userid,
        }
    )
    # print(f"获取表结构响应: {response.status_code}, {response.text}")
    if response.status_code == 200:
        return response.json().get("data", "")
    else:
        raise Exception(f"Failed to get table definition: {response.status_code}, {response.text}")

def query_data(host: str, token: str, userid: str, sql: str, table: str) -> any:
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(
        url=f"{host}/api/oauthaccess/datav/agent/queryData",
        headers=headers,
        json={
            "userid": userid,
            "sql": sql,
            "dataset": table
        }
    )
    if response.status_code == 200:
        return response.json().get("data", "")
    else:
        raise Exception(f"Failed to query data: {response.status_code}, {response.text}")