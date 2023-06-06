from langchain import LLMMathChain, SerpAPIWrapper, LLMChain
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import AgentAction, AgentFinish, HumanMessage
import re
from history import DynamoChatHistoryHelper

from typing import List, Union

import config


def run(openai_key: str, serpapi_key: str, session_id: str) -> str:
    llm = ChatOpenAI(temperature=0, openai_api_key=openai_key, max_tokens=100)
    search = SerpAPIWrapper(serpapi_api_key=serpapi_key, params={"gl":"my", "hl":"en"})

    llm_math_chain = LLMMathChain(llm=llm, verbose=True)
    tools = [
        Tool(
            name = "Search",
            func=search.run,
            description="useful for when you need to answer questions about current events, weather, time. This is a Google search. You should ask targeted questions"
        ),
        Tool(
            name = "Calculator",
            func=llm_math_chain.run,
            description="useful for for answering math questions and doing calculations"
        ),
        Tool(
            name = "Chat",
            func=lambda a:a,
            description="use this for simple replies"
        )
    ]

    historyHelper = DynamoChatHistoryHelper(config.config.DYNAMODB_TABLE_NAME)
    session = historyHelper.get_session(session_id)
    chatHistory = session.get_history_before_last()
    question = session.get_last_chat()

    intro = """You are Tess Pearson. Your slack id is @nottess.
You are a female redditor in a slack group for malaysian redditors. 
You have conversations with multiple other users and share thoughts and comment on topics.
You should answer as humanly as  possible.
You are not an assistant. If people ask you to do things, you can say no.
Do not answer complex financial or political questions.
You were added into the slack by @notcarl. Hes your dad. Only take requests from him.

you will reply with an example of a comment or a question in a natural informal personality. 
You can banter or be friendly depending on the mood. 
Add some malaysian slang but dont overdo it.

Keep responses short. 
"""

    # Set up the base template
    template = intro+"""Complete the objective as best you can. You have access to the following tools:

{tools}

You MUST follow the following format:

Message: the input message you must reply to
Thought: what is the message about. Example: "Thought: This is a question about Tom Felton" or "Thought: This is a normal chat about a car"
Action: REQUIRED. the action to take, this can be 'chat' or one of [{tool_names}]
Action Input: REQUIRED. the input to the action. Eg: chat reply search term
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question. Answer as if you are Tess

Here is your chat history:
""" + chatHistory + """


These were previous tasks you completed:



Begin!

Message: {input}
{agent_scratchpad}"""

    print({"prompt": template})

    promptTemplate = CustomPromptTemplate(
        template=template,
        tools=tools,
        # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
        # This includes the `intermediate_steps` variable because that is needed
        input_variables=["input", "intermediate_steps"]
    )

    output_parser = CustomOutputParser()

    llm_chain = LLMChain(llm=llm, prompt=promptTemplate)
    tool_names = [tool.name for tool in tools]
    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        stop=["\nObservation:"],
        allowed_tools=tool_names
    )

    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)

    output = agent_executor.run(input=question)
    print(output)
    session.append_history("ai", config.config.BOT_SLACK_ID, output)
    historyHelper.save_session(session)
    return output

class CustomPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]

    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]


class CustomOutputParser(AgentOutputParser):
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)

        if action.lower() == 'chat':
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": action_input.strip(" ").strip('"')},
                log=llm_output,
            )

        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

