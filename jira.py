# jira.py

from requests.auth import HTTPBasicAuth
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import requests, json, os

load_dotenv()

class Jira(ABC):

    def _request_jira(self, kwargs):

        JIRA_URL = os.getenv('JIRA_URL', '').strip('/')
        JIRA_USER = os.getenv('JIRA_USER', '')
        JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', '')

        if not JIRA_URL or not JIRA_USER or not JIRA_API_TOKEN:
            raise ValueError("Environment variables JIRA_URL, JIRA_USER, and JIRA_API_TOKEN must be set.")

        kwargs['url'] = f'{JIRA_URL}/rest/api/3/{kwargs.pop('context_path').strip('/')}'
        kwargs['data'] = json.dumps(kwargs.pop('payload', None))
        kwargs['headers'] = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        kwargs['auth'] = HTTPBasicAuth(
                username=JIRA_USER,
                password=JIRA_API_TOKEN
        )

        try:
            response = requests.request(**kwargs)
            
            if response.status_code == 200:
                return response.json()

            elif response.status_code == 204:
                return None

            else:
                response.raise_for_status()  # This raises an HTTPError for non-200, non-204 status codes

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            raise

        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            raise

        except ValueError as json_err:
            print(f"JSON decode error: {json_err}")
            raise

    @abstractmethod
    def _get_data(self):
        pass