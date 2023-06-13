import boto3


class PromptVersion:
    def __init__(self, intro, prompt_id):
        self.prompt_id = prompt_id
        self.intro = intro

    def to_dict(self):
        return {
            'PromptId': self.prompt_id,
            'Intro': self.intro
        }

    @classmethod
    def from_dict(cls, item):
        return cls(
            prompt_id=item['PromptId'],
            intro=item['Intro']
        )

class DynamoPromptHelper:
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

    def get_prompt(self, prompt_id):
        json = self.get_item({'PromptId': prompt_id})
        if json:
            return PromptVersion.from_dict(json)
        return json
