import httpx

def send_post_request(name):
    url = f"https://functions.yandexcloud.net/d4ekuoccv9lmm79dh5rr?name={name}"
    with httpx.Client() as client:
        response = client.get(url)
        # print(f"Status Code: {response.status_code}")
        # print(f"Response Content: {response.text}")
        return response.text
    
if __name__ == "__main__":
    name = "Master"
    send_post_request(name)