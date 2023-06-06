import boto3
import time
from typing import List
from decimal import Decimal

class ChatMessage:
    def __init__(self, userType, user, content):
        self.userType = userType
        self.user = user
        self.content = content

    def to_string(self):
        return self.user + "(" + self.userType + "): " + self.content

    def to_dict(self):
        return {
            'UserType': self.userType,
            'User': self.user,
            'Content': self.content,
        }

    @classmethod
    def from_dict(cls, item):
        return cls(
            userType=item['UserType'],
            user=item['User'],
            content=item['Content']
        )


class ChatSession:
    def __init__(self, sessionId: str, history: List[ChatMessage], lastEventId: str, lastTagged = Decimal(str(time.time()))):
        self.sessionId = sessionId
        self.history = history
        self.lastTagged = lastTagged
        self.lastEventId = lastEventId

    def get_last_chat(self):
        return self.history[-1].to_string()

    def get_history_before_last(self):
        history_before_last = self.history[:-1]
        if history_before_last:
            return "\n".join([item.to_string() for item in self.history[:-1]])
        return ""

    def append_history(self, userType, user, content):
        self.history.append(ChatMessage(userType, user, content))
        new_history = self.history[-10:]
        self.history = new_history

    def newTag(self):
        self.lastTagged = Decimal(str(time.time()))

    def to_dict(self):
        return {
            'SessionId': self.sessionId,
            'History': [item.to_dict() for item in self.history],
            'LastEventId': self.lastEventId,
            'LastTagged': self.lastTagged,
        }

    @classmethod
    def from_dict(cls, item):
        items = [ChatMessage.from_dict(sub_item) for sub_item in item['History']]
        return cls(
            sessionId=item['SessionId'],
            history=items,
            lastEventId=item['LastEventId'],
            lastTagged=item['LastTagged']
        )


class DynamoChatHistoryHelper:
    def __init__(self, table_name):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def put_item(self, item):
        """
        Function to write an item into DynamoDB.
        :param item: item to be written (Python dictionary)
        """
        self.table.put_item(Item=item)

    def get_item(self, key):
        """
        Function to read an item from DynamoDB.
        :param key: primary key dictionary of the item to be read
        """
        response = self.table.get_item(Key=key)
        return response.get('Item')

    def query_items(self, index_name, key_condition_expression):
        """
        Function to query multiple items from DynamoDB based on an index.
        :param index_name: Name of the index to be used for the query
        :param key_condition_expression: Key condition for the query
        """
        response = self.table.query(
            IndexName=index_name,
            KeyConditionExpression=key_condition_expression
        )
        return response['Items']

    def delete_item(self, key):
        """
        Function to delete an item from DynamoDB.
        :param key: primary key dictionary of the item to be deleted
        """
        self.table.delete_item(Key=key)

    def get_session(self, sessionId):
        json = self.get_item({'SessionId': sessionId})
        if json:
            return ChatSession.from_dict(json)
        return json

    def save_session(self, chatSession: ChatSession):
        self.put_item(chatSession.to_dict())
