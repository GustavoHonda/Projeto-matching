import requests
from dotenv import load_dotenv
import os
from abc import ABC, abstractmethod
import json


class GetMsg:
    @abstractmethod
    def get_messages(self):
        pass


class Whapi_getter(GetMsg):
    def __init__(self):
        load_dotenv()
        self.api_url = os.getenv("API_URL")
        self.token = os.getenv("TOKEN")

    def get_messages(self,phone, count=100, time_from=None, time_to=None):
        url = f"{self.api_url}/messages/list?count=100&time_from={time_from}&time_to={time_to}&author={phone}"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.token}"
        }
        response = requests.get(url, headers=headers)
        return response.json()
    

def main():
    getter = Whapi_getter()
    messages = getter.get_messages(phone=5511976154853,time_from=1751697978, time_to=1752697978)
    json.dump(messages, open("messages.json", "w"), indent=4, ensure_ascii=False)
    print(messages)


if __name__ == "__main__":
    main()