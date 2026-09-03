# src/main.py

from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_astradb import AstraDBVectorStore
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain.tools.retriever import create_retriever_tool
from langchain import hub
from github import fetch_github_issues, fetch_default_branch, fetch_repo_tree, filter_code_files, load_code
from note import note_tool

load_dotenv()

def connect_to_vstore(collection_name):
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
        collection_name = collection_name,
        api_endpoint = ASTRA_DB_API_ENDPOINT,
        token = ASTRA_DB_APPLICATION_TOKEN,
        namespace = ASTRA_DB_KEYSPACE,
    )
    
    return vstore

issue_vstore = connect_to_vstore("github")
code_vstore = connect_to_vstore("github_code")

owner = input("Enter the owner of the repository: ")
repo = input("Enter the repository name: ")

branch = fetch_default_branch(owner, repo)

print("Default branch:", branch)

tree = fetch_repo_tree(owner, repo, branch)

files = filter_code_files(tree)

print("Files:")
for file in files:
    print(file)

code_docs = load_code(
    owner,
    repo,
    branch,
    files
)

print("Number of documents:", len(code_docs))

code_vstore.add_documents(code_docs)

want_to_update_vectorstore = input("Do you want to update the issues? (y/N): ")
while want_to_update_vectorstore != "y" and want_to_update_vectorstore != "N":
    want_to_update_vectorstore = input("Invalid input. Do you want to update the issues? (y/N): ")
if want_to_update_vectorstore == "y":
    want_to_update_vectorstore = True
else:
    want_to_update_vectorstore = False

if want_to_update_vectorstore:
    issues = fetch_github_issues(owner, repo)

    if issues is None:
        print("Failed to fetch issues. Please check the repository details and try again.")
        raise SystemExit(1)

    try:
        issue_vstore.delete_collection()
    except:
        pass

    issue_vstore = connect_to_vstore("github")
    issue_vstore.add_documents(issues)

    # results = vstore.similarity_search("flash messages", k = 3)
    # for result in results:
    #     print(f"* {result.page_content} {result.metadata}")

retriever = issue_vstore.as_retriever(
    # search_type = "similarity" (assumed default),
    search_kwargs = {"k": 3}
)

retriever_tool = create_retriever_tool(
    retriever,
    "github_search",
    "Search for information about github issues. For any questions about github issues, you must use this tool!",
)

code_retriever = code_vstore.as_retriever(
    # search_type = "similarity" (assumed default),
    search_kwargs = {"k": 3}
)

code_tool = create_retriever_tool(
    code_retriever,
    "code_search",
    "Search the repository source code and documentation. "
    "Use this tool for questions about how the repository "
    "works, what the code does, or how different parts of "
    "the repository are implemented."
)

prompt = hub.pull(
    "hwchase17/openai-functions-agent",
)

llm = ChatOpenAI(
    model = "gpt-4o-mini",
    temperature = 0,
    max_tokens = 700
    )

tools = [retriever_tool, code_tool, note_tool]
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent = agent, tools = tools, verbose = False)

while True:
    question = input("Ask a question about github issues (q to quit): ")
    if question == "q":
        break

    result = agent_executor.invoke({"input": question})
    print(result["output"])