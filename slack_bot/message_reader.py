import json

import boto3

from models import SlackMessage
from history import DynamoChatHistoryHelper, ChatSession

import config
import utils
import time
import random


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Lambda handler that reads the messages from slack and
    distributes them to an sqs queue or DynamoDB store based on 
    whether message was directly addressed to the bot (a message
    that starts with `@bot-name`) or a conversation between two
    or more slack users. Note that the conversation history is only
    stored after the first direct message to the bot is received.
    """

    body = json.loads(event['body'])

    logging.debug(body)

    # For initial validation call from slack
    if "challenge" in body:
        challenge = body["challenge"]
        return utils.build_response({"challenge": challenge})

    sqs = boto3.client('sqs')
    queue_url = sqs.get_queue_url(
        QueueName=config.config.MESSAGE_QUEUE_NAME,
    )

    slack_message = SlackMessage(body)
    print('slack_message', body)
    print('slack_message.channel', slack_message.channel)
    history_helper = DynamoChatHistoryHelper(config.config.CHAT_HISTORY_TABLE_NAME)
    session = history_helper.get_session(slack_message.channel)
    if not session:
        session= ChatSession(sessionId=slack_message.channel, history=[], lastEventId="")

    logging.debug(f"Thread id is {slack_message.channel}")

    tag_expiry = session.lastTagged + 30 * 60

    print('direct message', slack_message.is_direct_message())
    random_run = random.randint(0, 1) == 1
    print('random_run', random_run)
    tag_not_expired = tag_expiry > time.time()
    print('tag_not_expired', tag_not_expired)
    last_event_id = session.lastEventId if session.lastEventId else ""

    print('slack_message.is_bot_reply()', slack_message.is_bot_reply())
    print('last_event_id != slack_message.event_id', last_event_id != slack_message.event_id)

    try:
        if not slack_message.is_bot_reply() and last_event_id != slack_message.event_id:
            print(f"Saving message with event_id: {slack_message.event_id} to history")
            print(slack_message.sanitized_text())
            # add to memory for context
            if slack_message.sanitized_text():
                session.append_history(
                    userType="human",
                    user=slack_message.user,
                    content=slack_message.sanitized_text())

            session.lastEventId = slack_message.event_id
            if slack_message.is_direct_message():
                session.newTag()

            history_helper.save_session(session)

            if slack_message.is_direct_message() or (random_run and tag_not_expired):
                logging.info(f"Sending message with event_id: {slack_message.event_id} to queue")
                print("triggering message")
                # send to queue
                sqs.send_message(
                    QueueUrl=queue_url["QueueUrl"],
                    MessageBody=(event['body']),
                    MessageGroupId=str(slack_message.channel),
                    MessageDeduplicationId=slack_message.event_id
                )


        logging.info(f"Done processing message with event id: {slack_message.event_id}")
    except Exception as e:
        logging.error(e)

    return utils.build_response("Processed message successfully!")

