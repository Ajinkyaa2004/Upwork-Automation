import requests
import time
from .config import config

class UpworkClient:
    TOKEN_URL = "https://www.upwork.com/api/v3/oauth2/token"
    GRAPHQL_URL = "https://api.upwork.com/graphql"

    def __init__(self):
        self.access_token = None
        self.token_expires_at = 0

    def _get_access_token(self):
        if self.access_token and time.time() < self.token_expires_at - 60:
            return self.access_token

        data = {
            "grant_type": "client_credentials",
            "client_id": config.UPWORK_CLIENT_ID,
            "client_secret": config.UPWORK_CLIENT_SECRET,
        }
        resp = requests.post(self.TOKEN_URL, data=data, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()
        self.access_token = token_data["access_token"]
        self.token_expires_at = time.time() + token_data.get("expires_in", 86400)
        return self.access_token

    def graphql(self, query: str, variables: dict = None):
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if config.UPWORK_TENANT_ID:
            headers["X-Upwork-API-TenantId"] = config.UPWORK_TENANT_ID

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        resp = requests.post(self.GRAPHQL_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        return result.get("data")

    def get_company_selector(self):
        query = """
        query {
          companySelector {
            items {
              title
              organizationId
            }
          }
        }
        """
        return self.graphql(query)

    def list_rooms(self, limit: int = 20):
        query = """
        query ListRooms($pagination: Pagination) {
          roomList(pagination: $pagination, sortOrder: DESC) {
            edges {
              node {
                id
                roomName
                topic
                numUnread
                lastVisitedDateTime
              }
            }
          }
        }
        """
        variables = {"pagination": {"first": limit}}
        return self.graphql(query, variables)

    def get_room_stories(self, room_id: str, limit: int = 20):
        query = """
        query RoomStories($filter: RoomStoryFilter!) {
          roomStories(filter: $filter) {
            edges {
              node {
                id
                message
                createdDateTime
                user { id name }
              }
            }
          }
        }
        """
        variables = {
            "filter": {
                "roomId_eq": room_id,
                "pagination": {"first": limit}
            }
        }
        return self.graphql(query, variables)

    def send_message(self, room_id: str, message: str):
        mutation = """
        mutation SendRoomMessage($input: RoomStoryCreateInputV2!) {
          createRoomStoryV2(input: $input) {
            id
            message
          }
        }
        """
        variables = {
            "input": {
                "roomId": room_id,
                "message": message
            }
        }
        return self.graphql(mutation, variables)

upwork = UpworkClient()
