class ClearGuideApiHandler:
    import requests

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.refresh_token = None
        self.access_token = None
        self.authenticate()

    def authenticate(self):
        data = {"username": self.username, "password": self.password}
        response = self.requests.post('https://auth.iteris-clearguide.com/api/token/', data=data)
        if response.status_code == 200:
            response_dict = response.json()
            self.refresh_token = response_dict.get('refresh')
            self.access_token = response_dict.get('access')
            if self.refresh_token and self.access_token:
                return True
        raise Exception(
            f"Error while authenticating... Status Code: {response.status_code} Message: {response.text}")

    def refresh_access_token(self):
        data = {"refresh": self.refresh_token}
        response = self.requests.post('https://auth.iteris-clearguide.com/api/token/refresh/', data=data)
        if response.status_code == 200:
            self.access_token = response.json().get('access')
        else:
            return self.authenticate()

    @property
    def auth_header(self):
        return {'Authorization': f'Bearer {self.access_token}'}

    def call(self, url):
        response = self.requests.get(url=url, headers=self.auth_header)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401 or response.status_code == 403:
            self.refresh_access_token()
            return self.call(url)
        else:
            raise Exception(
                f"Error fetching response from ClearGuide... Status Code: {response.status_code} Message: {response.text}")
