import getpass
import os, re ,uuid
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from typing import List, TypedDict
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()

if not os.environ.get("OPENAI_KEY"):
  os.environ["OPENAI_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

llm = init_chat_model("gpt-4o-mini", model_provider="openai")

emb = OpenAIEmbeddings(model="text-embedding-3-large")


# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

state: State = {
        "question": "",
        "context": [],
        "answer": ""
    }


def make_clean_file_name(name)-> str:
    """Clean filename from special characters, turn it to hash format and return it"""
    file_name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    file_name = file_name.strip().lower()
    file_name = re.sub(r"[^A-Za-z0-9._-]", "_", file_name)
    return file_name


def create_source_key(username:str, file_name:str) ->str:
    """Creates a unique and safe source key for a file based on user_id and file name."""
    unique_file_id = str(uuid.uuid4())
    #To prevent special character that might cause problem for ChromaDB
    safe_file_name = make_clean_file_name(file_name)
    source_key = f"user_{username}_{unique_file_id}_{safe_file_name}"
    return source_key


def get_user_store(user, emb=emb, distance_function="cosine") -> Chroma:
    """
       Return a per-user Chroma vector store handle.

       Creates (or opens, if it already exists) a Chroma collection that is isolated
       by user_id. The 'persist_directory' ensures vectors are stored on disk so they
       survive restarts. Passing the same embedding function guarantees that the
       embeddings used for indexing and querying are consistent.
       Returns:
           A Chroma vector store instance scoped to the given user.
       """
    basedir = os.path.abspath(os.path.dirname(__file__))
    chroma_path = os.path.join(basedir, f"../db/data/{user}")
    return Chroma(
        collection_name=f"user_{user}",
        persist_directory=chroma_path,
        collection_metadata={"hnsw:space": distance_function},
        embedding_function=emb
    )


def check_for_duplicate_document(username, raw_document: str, emb=emb, similarity_point: float = 0.98) -> bool:
    """
    Checks if a document with similar content already exists in the ChromaDB.
    It compares the new document with existing ones by using a representative sample
    of chunks from the new document.
    Returns:bool: True if a duplicate is found, False otherwise
    """
    vector_store = get_user_store(username, emb=emb, distance_function="cosine")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # chunk size (characters)
        chunk_overlap=200,  # chunk overlap (characters)
        add_start_index=True,  # track index in original document
    )
    new_chunks = text_splitter.split_documents([Document(page_content=raw_document)])
    if not new_chunks:
        print("Error: Document is empty or could not be processed.")
        return True  # Treat as duplicate to avoid errors
    chunks_to_compare = []
    num_chunks = len(new_chunks)
    if num_chunks <= 3:
        chunks_to_compare = new_chunks
        comparison_text = " ".join([chunk.page_content for chunk in chunks_to_compare])
        retrieved_docs = vector_store.similarity_search_with_score(comparison_text, k=1, filter={"username": username})
        if retrieved_docs:
            most_similar_document, distance = retrieved_docs[0]
            print("distance", distance)
            print("similarity_point", similarity_point)
            similarity = 1.0 - distance

            if similarity >= similarity_point:
                print(f"Document already exists with a similarity score of {similarity}.")
                return True
            else:
                print(f"No similar document found. The highest score was {similarity}.")
                return False

    else:
        chunks_to_compare.append(new_chunks[0])
        chunks_to_compare.append(new_chunks[num_chunks // 2])
        chunks_to_compare.append(new_chunks[num_chunks - 1])
        similarity_list = []
        for i in range(3):
            retrieved_docs = (vector_store.similarity_search_with_score(chunks_to_compare[i].page_content, k=1,
                                                                       filter={"username": username}))
            if retrieved_docs:
                doc, distance = retrieved_docs[0]
                similarity = 1.0 - distance
                similarity_list.append(similarity)
            else:
                similarity = 0
                similarity_list.append(similarity)
        if all(num > similarity_point for num in similarity_list):
            print(f"Document already exists with a similarity score of {similarity}.")
            return True

        else:
            print(f"No similar document found. The highest score was {similarity}.")
            return False

    print("No documents found for this user. This is a new document.")
    return False


def turn_txt_to_vector(username, raw_document, file_name, file_path, chunk_size: int = 1000, chunk_overlap: int = 200, emb=emb) ->int:

    vector_store = get_user_store(username, emb=emb)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, # chunk size (characters)
        chunk_overlap=chunk_overlap, # chunk overlap (characters)
        add_start_index=True,  # track index in original document
    )
    chunks = text_splitter.split_documents([Document(page_content=raw_document)])
    if not chunks:
        print("Error: Document is empty or could not be processed.")
        return 0
    document_id = str(uuid.uuid4())
    for chunk in chunks:
        # Generate a unique ID for the document
        chunk.metadata["username"] = username
        chunk.metadata["document_id"] = document_id
        chunk.metadata["source_key"] = create_source_key(username,file_name)
        chunk.metadata["file_name"] = file_name
        chunk.metadata["file_path"] = str(file_path)

    vector_store.add_documents(chunks)
    #Persist to disk so the index survives restarts
    vector_store.persist()

    return len(chunks)


# Define application steps
def retrieve_document(username, state: State = state, k=1):
    vector_store = get_user_store(username, emb=emb)
    retrieved_docs = vector_store.similarity_search(state["question"], k=k, filter={"username": username})
    return {"context": retrieved_docs}


def generate(state: State=state):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    prompt = ChatPromptTemplate.from_messages([
    ("system", "Use only the provided context. "
               "If insufficient, ask related question to gather more information that you need "
               "Output must be ONLY the answer in a few sentences)."),
    ("human",  "Question: {question}\n\nContext:\n{context}")
])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}


# Compile application and test
# graph_builder = StateGraph(State).add_sequence([retrieve, generate])
# graph_builder.add_edge(START, "retrieve")
# graph = graph_builder.compile()

# if __name__ == "__main__":
#     user = "test_user"
#
#
#     raw_text = """
#     my name is kulo I live in tourta. I am 25 yearsoll.
#     I love island.
#     """
#
#     # ۱) تبدیل متن به بردار و ذخیره
#     chunks_count = turn_txt_to_vector(user, raw_text)
#     print(f"✅ {chunks_count} chunks added to vector store.")
#
#     # ۲) ساخت State اولیه
#     state: State = {
#         "question": "where do I live?",
#         "context": [],
#         "answer": ""
#     }
#
#     ret_doc = retrieve(user, state)
#     state.update(ret_doc)
#     print(generate(state))