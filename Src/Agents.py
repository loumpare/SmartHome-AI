from langchain_core.prompts import ChatPromptTemplate

class SmartAgent:
    """
    A generic wrapper for LangChain agents.
    Handles system prompt orchestration and tool binding for specific LLM models.
    """
    def __init__(self, llm, name, system_prompt, tools=None):
        """
        Initializes the agent with a specific role and set of capabilities.
        
        Args:
            llm: The Language Model instance (e.g., ChatOpenAI).
            name (str): Technical name of the agent for logging purposes.
            system_prompt (str): The instructions defining the agent's behavior.
            tools (list, optional): List of @tool functions the agent can execute.
        """
        self.name = name
        
        # Define the message structure
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        # Bind tools to the model if provided, otherwise use the raw model
        # This allows the LLM to decide when to call external functions
        self.model = llm.bind_tools(tools) if tools else llm
        
        # Create the execution chain: Prompt -> Model
        self.chain = self.prompt | self.model

    def invoke(self, user_input):
        """
        Sends the user request through the chain.
        
        Args:
            user_input (str): The raw text query from the user.
        Returns:
            The model's response (either text or a tool call request).
        """
        return self.chain.invoke({"input": user_input})