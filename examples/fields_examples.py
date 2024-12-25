from jira2py import Jira
import os
from dotenv import load_dotenv

"""Load .env variables"""
load_dotenv()

"""Create a Jira instance"""
jira = Jira(
    url=os.getenv("JIRA_URL", ""),
    user=os.getenv("JIRA_USER", ""),
    api_token=os.getenv("JIRA_API_TOKEN", ""),
)

"""Get the list of Jira fields with its metadata"""
fields = jira.fields().get()
