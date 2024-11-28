import httpx

async def send_post_request(name):
    url = f"https://functions.yandexcloud.net/d4ekuoccv9lmm79dh5rr?name={name}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")

if __name__ == "__main__":
    import asyncio
    name = "Master"
    asyncio.run(send_post_request(name))