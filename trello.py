import requests
import json

from environs import Env
import exceptions

env = Env()
env.read_env()


class TrelloManager:
    KEY = env("TRELLO_KEY")
    TOKEN = env("TRELLO_TOKEN")

    def __init__(self, username):
        self.username = username

    @staticmethod
    def base_headers():
        return {
            "Accept": "application/json"
        }

    def credentials(self):
        return {
            "key": self.KEY,
            "token": self.TOKEN
        }

    def get_member_id(self):
        url = f"https://api.trello.com/1/members/{self.username}"

        response = requests.request(
            "GET",
            url,
            headers=self.base_headers(),
            params=self.credentials()
        )
        if response.status_code == 200:
            return json.loads(response.text)

    def create_new_boards(self, board_name):

        url = "https://api.trello.com/1/boards/"

        params = {'name': {board_name}}
        params.update(self.credentials())

        response = requests.request(
            "POST",
            url,
            params=params
        )
        if response.status_code == 200:
            return json.loads(response.text)

    def get_boards(self):
        url = f"https://api.trello.com/1/members/{self.username}/boards"

        response = requests.request(
            "GET",
            url,
            headers=self.base_headers(),
            params=self.credentials()
        )
        if response.status_code == 200:
            return json.loads(response.text)

    def get_lists_on_a_board(self, board_id):
        url = f"https://api.trello.com/1/boards/{board_id}/lists"

        response = requests.request(
            "GET",
            url,
            headers=self.base_headers(),
            params=self.credentials()
        )
        if response.status_code == 200:
            return json.loads(response.text)

    def get_cards_on_a_list(self, list_id):
        url = f"https://api.trello.com/1/lists/{list_id}/cards"

        response = requests.request(
            "GET",
            url,
            headers=self.base_headers(),
            params=self.credentials()
        )
        if response.status_code == 200:
            return json.loads(response.text)

    def get_board_id_with_name(self, name):
        try:
            return [board.get("id") for board in self.get_boards() if board.get("name") == name][0]
        except IndexError as e:
            print(e)

    @staticmethod
    def get_list_id_with_name(list_data, name):
        try:
            return [data.get("id") for data in list_data if data.get("name") == name][0]
        except IndexError as e:
            exceptions.write_exceptions(e)

    def get_board_members(self, board_id):

        url = f"https://api.trello.com/1/boards/{board_id}/memberships"

        response = requests.request(
            "GET",
            url,
            headers=self.base_headers(),
            params=self.credentials()
        )

        if response.status_code == 200:
            return json.loads(response.text)

    def get_fullname_in_members(self, members_id):
        url = f"https://api.trello.com/1/members/{members_id}"

        response = requests.request(
            "GET",
            url,
            headers=self.base_headers(),
            params=self.credentials()
        )

        if response.status_code == 200:
            return json.loads(response.text)

    def create_new_card(self, params):

        url = "https://api.trello.com/1/cards"

        params.update(self.credentials())

        response = requests.request(
            "POST",
            url,
            headers=self.base_headers(),
            params=params
        )

        if response.status_code == 200:
            return json.loads(response.text)

    def get_labels_board(self, board_id):
        url = f"https://api.trello.com/1/boards/{board_id}/labels"

        response = requests.request(
            "GET",
            url,
            params=self.credentials()
        )

        if response.status_code == 200:
            return json.loads(response.text)

    def create_new_labels(self, params):
        url = "https://api.trello.com/1/labels"

        params.update(self.credentials())

        response = requests.request(
            "POST",
            url,
            params=params
        )
        if response.status_code == 200:
            return json.loads(response.text)

    def add_label_to_card(self, card_id, label_id):
        url = f"https://api.trello.com/1/cards/{card_id}/idLabels"
        params = {**self.credentials(), "value": label_id}
        response = requests.request('POST', url, params=params)
        if response.status_code == 200:
            return json.loads(response.text)

    def add_a_member_to_card(self, card_id, member_id):

        url = f"https://api.trello.com/1/cards/{card_id}/idMembers"
        params = {**self.credentials(), "value": member_id}

        response = requests.request(
            "POST",
            url,
            params=params
        )
        if response.status_code == 200:
            return json.loads(response.text)
