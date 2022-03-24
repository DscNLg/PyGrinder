import logging
import aiohttp
import time
from scheduler import schedule

class Author:
    def __init__(self, json) -> None:
        self.id = json["id"]
        self.username = json["username"]
        self.discriminator = json["discriminator"]

class EmbedField:
    def __init__(self, json) -> None:
        self.name = json["name"]
        self.value = json["value"]

class Embed:
    def __init__(self, json) -> None:
        self.title = json.get("title")
        self.author = json.get("author")
        self.description = json.get("description")
        self.fields = [EmbedField(field) for field in json["fields"]]

class Reference:
    def __init__(self, json) -> None:
        self.message_id = json["message_id"]
        self.message = MessageClass(json["resolved"])

class Button:
    def __init__(self, json) -> None:
        self.custom_id = json["custom_id"]
        self.disabled = json["disabled"]
        self.emoji = json["emoji"]
        self.label = json["label"]

class MessageClass:
    def __init__(self, message_json) -> None:
        self.id = message_json["id"]
        self.content = message_json.get("content")
        self.channel_id = message_json["channel_id"]
        self.guild_id = message_json["guild_id"]
        self.author = Author(message_json["author"])
        self.embed = Embed(message_json["embeds"][0]) if message_json.get("embeds") else None
        self.reference = Reference(message_json["reference"]) if message_json.get("reference") else None
        self.components = [Button(component) for component in message_json["components"][0]]

class Instance:
    def __init__(self, config: dict, sessions) -> None:
        self.id: int = config["id"]
        self.token: str = config["token"]
        self.grind_channel_id: int = config["grind_channel_id"]
        self.master_id: int = config["master_id"]
        self.response_timeout: int = config["response_timeout"]
        self.queue: schedule.Q() = config["queue"]

        self.coins: int = config["coins"]
        self.items: dict = config["items"] # {item: amount}

        self.ws = config["ws"]
        self.heartbeat_interval: int = config["heartbeat_interval"]
        self.session: aiohttp.ClientSession = sessions.session

        self.logger: logging.Logger = config["logger"]
        self.voting_session: aiohttp.ClientSession = sessions.voting_session

        self._search_preference: list = config["_search_preference"]
        self._search_cancel: list = config["_search_cancel"]
        self._search_timeout: int = config["_search_timeout"]

        self._crime_preference: list = config["_crime_preference"]
        self._crime_cancel: list = config["_crime_cancel"]
        self._crime_timeout: int = config["_crime_timeout"]

    def _update_balance(self, amount, task):
        if task == "ADD":
            self.coins -= amount
        elif task == "REM":
            self.coins -= amount
        return self.coins

    def _update_items(self, *items, task):
        for item in items:
            if task == "ADD":
                self.items[0] += item[1]
            elif task == "REM":
                self.items[0] -= item[1]
        return self.items

    def default(event, send_message_json):
        return event["d"]["author"]["id"] == 270904126974590976 and event["d"]["referenced_message"] is not None and str(event["d"]["referenced_message"]["id"]) == str(send_message_json["id"])

    async def wait_for(self, event_type, predicate, send_message_json):
        start = time.time()
        if predicate == "default": # must reference
            predicate = self.default
        while time.time() - start < self.response_timeout:
            event = self.ws.recv()
            if event["t"] == event_type and predicate(event, send_message_json):
                return 200, MessageClass(event["d"])
        else:
            return 408, None
