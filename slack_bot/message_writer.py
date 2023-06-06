import json

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from models import SlackMessage
import chain

import utils

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Lambda handler that pulls the messages from the
    sqs queue, and calls the LLM chain to process the
    user's message. This lambda writes the response from
    the LLM chain to the slack thread.
    """

    logging.debug(event)

    record = event['Records'][0]
    body = json.loads(record['body'])
    slack_message = SlackMessage(body=body)

    try:
        # SECRETS = utils.get_secrets()
        API_KEY = "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"
        SLACK_TOKEN = "xoxb-68007742017-5356814587254-WjqoB9ZR2waQUAjSnvPmi8yW"
        SERPAPI_KEY = "c1f5b8d12c5d1c3ff3bbae9f28fee09309201013a76e76f32ac138c32ae2c460"

        logging.info(f"Sending message with event_id: {slack_message.event_id} to LLM chain")

        response_text = chain.run(
            openai_key=API_KEY,
            serpapi_key=SERPAPI_KEY,
            session_id=slack_message.channel
        )

        client = WebClient(token=SLACK_TOKEN)

        logging.info(f"Writing response for message with event_id: {slack_message.event_id} to slack")

        client.chat_postMessage(
            channel=slack_message.channel,
            text=response_text
        )
    except SlackApiError as e:
        assert e.response["error"]
        logging.error(e)

    return utils.build_response("Processed message successfully!")

