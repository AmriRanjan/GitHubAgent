from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_astradb import AstraDBVectorStore
from langchain_core.tools.retriever import create_retriever_tool
from github import fetch_github_issues
from note import note_tool
from langchain.agents import create_agent

load_dotenv()

def connect_to_vstore():
    embeddings = OpenAIEmbeddings()
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
    ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    desired_namespace = os.getenv("ASTRA_DB_KEYSPACE")

    if desired_namespace:
        ASTRA_DB_KEYSPACE = desired_namespace
    else:
        ASTRA_DB_KEYSPACE = None

    vstore = AstraDBVectorStore(
        embedding = embeddings,
        collection_name = "github",
        api_endpoint = ASTRA_DB_API_ENDPOINT,
        token = ASTRA_DB_APPLICATION_TOKEN,
        namespace = ASTRA_DB_KEYSPACE,
    )
    
    return vstore


vstore = connect_to_vstore()
want_to_update_vectorstore = input("Do you want to update the issues? (y/N): ").lower() in [
    "yes",
    "y",
]

if want_to_update_vectorstore:
    owner = input("Enter the GitHub username: ")
    repo = input("Enter the repository name: ")
    issues = fetch_github_issues(owner, repo)

    try:
        vstore.delete_collection()
    except:
        pass

    vstore = connect_to_vstore()
    vstore.add_documents(issues)

    results = vstore.similarity_search("flash messages", k = 3)
    for result in results:
        print(f"* {result.page_content} {result.metadata}")

retriever = vstore.as_retriever(
    search_type = "similarity",
    search_kwargs = {"k": 3}
)

retriever_tool = create_retriever_tool(
    retriever,
    "github_search",
    "Search for information about github issues. For any questions about github issues, you must use this tool!",
)

llm = ChatOpenAI()

tools = [retriever_tool, note_tool]

agent = create_agent(
    model = llm,
    tools = tools
)

# prompt = hub.pull("hwchase17/openai-functions-agent")
# llm = ChatOpenAI()

# tools = [retriever_tool, note_tool]
# agent = create_tool_calling_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(agent = agent, tools = tools, verbose = False)

question = input("Ask a question about github issues (q to quit): ")

while question != "q":
    result = agent.invoke({
        "messages": [
            {"role": "user", "content": question}
        ]
    })

    print(result["messages"][-1].content)
    question = input("Ask a question about github issues (q to quit): ")