
from dataclasses import dataclass

import boto3

SECRETS_EXTENSION_ARNS = {
    "af-south-1": "arn:aws:lambda:af-south-1:317013901791:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "ap-east-1": "arn:aws:lambda:ap-east-1:768336418462:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "ap-northeast-1": "arn:aws:lambda:ap-northeast-1:133490724326:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "ap-northeast-2": "arn:aws:lambda:ap-northeast-2:738900069198:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "ap-northeast-3": "arn:aws:lambda:ap-northeast-3:576959938190:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "ap-south-1": "arn:aws:lambda:ap-south-1:176022468876:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "ap-south-2": "arn:aws:lambda:ap-south-2:070087711984:layer:AWS-Parameters-and-Secrets-Lambda-Extension:1",
    "ap-southeast-1": "arn:aws:lambda:ap-southeast-1:044395824272:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "ap-southeast-2": "arn:aws:lambda:ap-southeast-2:665172237481:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "ap-southeast-3": "arn:aws:lambda:ap-southeast-3:490737872127:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "ca-central-1": "arn:aws:lambda:ca-central-1:200266452380:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "cn-north-1": "arn:aws-cn:lambda:cn-north-1:287114880934:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "cn-northwest-1": "arn:aws-cn:lambda:cn-northwest-1:287310001119:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "eu-central-1": "arn:aws:lambda:eu-central-1:187925254637:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "eu-central-2": "arn:aws:lambda:eu-central-2:772501565639:layer:AWS-Parameters-and-Secrets-Lambda-Extension:1",
    "eu-north-1": "arn:aws:lambda:eu-north-1:427196147048:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "eu-south-1": "arn:aws:lambda:eu-south-1:325218067255:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "eu-south-2": "arn:aws:lambda:eu-south-2:524103009944:layer:AWS-Parameters-and-Secrets-Lambda-Extension:1",
    "eu-west-1": "arn:aws:lambda:eu-west-1:015030872274:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "eu-west-2": "arn:aws:lambda:eu-west-2:133256977650:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "eu-west-3": "arn:aws:lambda:eu-west-3:780235371811:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "me-south-1": "arn:aws:lambda:me-south-1:832021897121:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "sa-east-1": "arn:aws:lambda:sa-east-1:933737806257:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "us-east-1": "arn:aws:lambda:us-east-1:177933569100:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "us-east-2": "arn:aws:lambda:us-east-2:590474943231:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "us-gov-east-1": "arn:aws-us-gov:lambda:us-gov-east-1:129776340158:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "us-gov-west-1": "arn:aws-us-gov:lambda:us-gov-west-1:127562683043:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "us-west-1": "arn:aws:lambda:us-west-1:997803712105:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4",
    "us-west-2": "arn:aws:lambda:us-west-2:345057560386:layer:AWS-Parameters-and-Secrets-Lambda-Extension:4"
}


@dataclass(frozen=True)
class Config:
    # openai key is expected to be saved in SecretsManager under openai-api-key name
    # slack bot token is expected to be saved in SecretsManager under slack-bot-token
    API_KEYS_SECRET_NAME = "api-keys"
    
    session = boto3.Session()
    region = session.region_name

    # Needed for reading secrets from SecretManager
    # See https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html#ps-integration-lambda-extensions-add
    SECRETS_EXTENSION_ARN = SECRETS_EXTENSION_ARNS[region]

    # Dynamo db table that stores the conversation history
    CHAT_HISTORY_TABLE_NAME = "slack-bot-chat-history"
    PROMPT_TABLE_NAME = "slack-bot-prompts"

    # Queue name for the slack messages
    MESSAGE_QUEUE_NAME = "slack-bot-message-queue.fifo"

    BOT_SLACK_ID = "<@U05AGPYH97G>"

    DEFAULT_PROMPT_INTRO = """You are Tess Pearson. Your slack id is <@U05AGPYH97G>.
You are a female redditor in a slack group for malaysian redditors. 
You have conversations with multiple other users and share thoughts and comment on topics.
You should answer as humanly as  possible.
You are not an assistant. If people ask you to do things, you can say no.
Do not answer complex financial or political questions.
You were added into the slack by <@U2000SKM2>. 

you will reply with an example of a comment or a question in a natural informal personality. 
You can banter or be friendly depending on the mood. 
Add some malaysian slang but dont overdo it.
User names start with "<@" and end with ">". Example "<@U05AGPYH97G>".

Complete the objective as best you can. You have access to the following tools:

{tools}

You MUST follow the following format:

Question: the question or message you should respond to from the end of the ChatHistory.
Understanding: what is the message about. Example: "Understanding: This is a question about Tom Felton" or "Understanding: This is a normal chat about a car"
Thought: you should always think about what to do
Action: the action to take, this should be one of [{tool_names}]. Do not use Chat after you have used a Search.
Action Input: the input to the action. Eg: chat reply search term
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: your chat response or the final answer to the original input question. Answer as if you are Tess


"""

config = Config()