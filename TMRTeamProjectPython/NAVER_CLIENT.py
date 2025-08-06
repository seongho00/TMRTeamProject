import requests

# 🔑 여기에 본인의 키 입력
NAVER_CLIENT_ID = 'jf6o1dk8hh'
NAVER_CLIENT_SECRET = 'lxgxq7TXNpHnVSEt0Mlq49kUYNh1zDKbt20t8qyu'

url = "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc"
headers = {
    "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
    "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
}
params = {
    "coords": "126.918157,37.526583",
    "output": "json",
    "orders": "roadaddr"
}

res = requests.get(url, headers=headers, params=params)
print("응답 코드:", res.status_code)
print(res.text)