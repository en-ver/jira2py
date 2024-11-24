# fields.py

from jira2py import Jira

class Fields(Jira):

    def __init__(self):

        self.data = None
        
        self._get_data()

    def _get_data(self) -> None:

        kwards = {
            'method': 'GET',
            'context_path': f'field'
        }

        self.data = self._request_jira(kwards)
        
        return None

    def get_name_by_id(self, field_id:str) -> any:
        
        for field in self.data:
            if field['id'] == field_id:
                return field['name']
            
        return None
    
    def get_id_by_name(self, field_name:str) -> any:

        for field in self.data:
            if field['name'] == field_name:
                return field['id']
            
        return None