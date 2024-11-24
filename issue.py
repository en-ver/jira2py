# issue.py

from jira2py import Jira

class Issue(Jira):
    
    def __init__(self, key:str):
        
        self.data = None
        self.key = key
        self.names = None
        self.fields = None
        self.changelog = None

        self._get_data()
        
    def _get_data(self) -> None:

        kwargs = {
            'method': 'GET',
            'context_path': f'issue/{self.key}',
            'params': {
                'expand': 'names'
            }
        }

        self.data = self._request_jira(kwargs)
        self.key = self.data.get('key')
        self.names = self.data.get('names')
        self.fields = self.data.get('fields')
        
    def get_field_id(self, field: str) -> str:

        for key, value in self.names.items():
            if key == field or value == field:
                return key
        
        return None
    
    def get_field_value(self, field:str) -> any:
        
        field_id = self.get_field_id(field)
        
        for key, value in self.fields.items():
            if key == field_id:
                return value
        
        return None
    
    def get_changelog(self, field:str = None) -> list[dict]:
        
        start_at = 0
        changelog = []
        is_last = False
        
        while is_last is False:
        
            kwargs = {
                'method': 'GET',
                'context_path': f'issue/{self.key}/changelog',
                'params': {
                    'startAt': start_at
                }
            }

            response = self._request_jira(kwargs)

            start_at += response.get('maxResults')
            is_last = response.get('isLast')
            changelog.extend(response.get('values'))

        if field:
            changelog = [
                {**change, 'items': [item for item in change.get('items', []) if item.get('field') == field]}
                for change in changelog
                if any(item.get('field') == field for item in change.get('items', []))
            ]

        self.changelog = changelog

        return changelog

    def edit(self, fields:dict[any], notify_users:bool = False) -> 'Issue':
        
        for key in list(fields.keys()):
            field_id = self.get_field_id(key)
            fields[field_id] = fields.pop(key)

        kwargs = {
            'method': 'PUT',
            'context_path': f'issue/{self.key}',
            'params': {
                'notifyUsers': notify_users
            },
            'payload': {
                'fields': fields
            }
        }

        self._request_jira(kwargs)
        self._get_data()

        return self
