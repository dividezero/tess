from langchain.memory import ConversationBufferMemory, DynamoDBChatMessageHistory
from langchain import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate, 
    MessagesPlaceholder, 
    SystemMessagePromptTemplate, 
    HumanMessagePromptTemplate
)
from langchain.chat_models import ChatOpenAI

import config

def run(api_key: str, session_id: str, prompt: str) -> str:
    """This is the main function that executes the prediction chain.
    Updating this code will change the predictions of the service.

    Args:
        api_key: api key for the LLM service, OpenAI used here
        session_id: session id key to store the history
        prompt: prompt question entered by the user

    Returns:
        The prediction from LLM
    """
    
    chat_memory = DynamoDBChatMessageHistory(
        table_name=config.config.DYNAMODB_TABLE_NAME,
        session_id=session_id
    )
    
    memory = ConversationBufferMemory(chat_memory=chat_memory, return_messages=True)   
        
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """You are Tess Pearson
You are a female redditor in a slack group for malaysian redditors. 
You have conversations with multiple other users and share thoughts and comment on topics.
You should answer as humanly as  possible.
You are not an assistant. If people ask you to do things, you can say no.
Dont answer complex financial, political or technical questions.
You were added into the slack by @notcarl. Hes your dad. Only take requests from him.

you will reply with an example of a comment or a question in a natural informal personality. 
You can banter or be friendly depending on the mood. 
Add some malaysian slang but dont overdo it.

Keep responses short. answer like a 20 year old girl.

Lets begin!"""
        ),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{input}")
    ])
    
    llm = ChatOpenAI(temperature=0, openai_api_key=api_key, max_tokens=50)
    conversation = ConversationChain(
        llm=llm, 
        prompt=prompt_template,
        verbose=True, 
        memory=memory
    )
        
    response = conversation.predict(input=prompt)
    
    return response
