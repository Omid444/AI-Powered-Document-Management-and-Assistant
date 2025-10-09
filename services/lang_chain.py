import getpass
import os, re ,uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from typing import List, TypedDict
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
PROVIDER = "gemini"
#PROVIDER = "openai"
if PROVIDER == "openai":
    if not os.environ.get("OPENAI_KEY"):
        os.environ["OPENAI_KEY"] = getpass.getpass("Enter API key for OpenAI: ")
#llm = init_chat_model("gpt-4o-mini", model_provider="openai")

if PROVIDER == "gemini":
    if not os.environ.get("GOOGLE_API_KEY"):   # ✅ Gemini
        os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

#llm = init_chat_model("gpt-4o-mini", model_provider="openai")

# emb = OpenAIEmbeddings(model="text-embedding-3-large")
#emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001")  # ✅ Gemini

if PROVIDER == "openai":
    llm = init_chat_model("gpt-4o-mini", model_provider="openai")
    emb = OpenAIEmbeddings(model="text-embedding-3-large")
elif PROVIDER == "gemini":
    llm = init_chat_model("gemini-1.5-flash", model_provider="google_genai")   # ✅ Gemini LLM
    emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

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


def turn_txt_to_vector(username, raw_document, file_name, file_path, due_date, is_payment, is_tax_related, chunk_size: int = 1000, chunk_overlap: int = 200, emb=emb) ->int:

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
        chunk.metadata["due_date"] = due_date
        chunk.metadata["due_date_ts"] = datetime.fromisoformat(due_date).timestamp()
        chunk.metadata["is_payment"] = is_payment
        chunk.metadata["is_tax_related"] = is_tax_related
        chunk.metadata["is_closed"] = False


    vector_store.add_documents(chunks)
    #Persist to disk so the index survives restarts
    vector_store.persist()

    return len(chunks)



def retrieve_document(username, state: State = state, k=1):
    vector_store = get_user_store(username, emb=emb)
    retrieved_docs = vector_store.similarity_search(state["question"], k=k, filter={"username": username})
    return {"context": retrieved_docs}


def retrieve_due_date_documents(username):
    vector_store = get_user_store(username, emb=emb)
    today = datetime.now()
    a_month_from_now = today + timedelta(days=30)
    filter_query = {
        "$and": [
            {"username": username},
            {"due_date_ts": {"$gte": today.timestamp()}},
            {"due_date_ts": {"$lte": a_month_from_now.timestamp()}},
            {"is_closed": False}
        ]
    }
    results = vector_store.get(where=filter_query)
    unique_docs = {}
    print("-------resluts",results)
    for meta, doc in zip(results["metadatas"], results["documents"]):
        doc_id = meta.get("document_id")
        # Looking for starting_index with 0 value
        if meta.get("start_index", 9999) == 0:
            unique_docs[doc_id] = {
                "metadata": meta,
                "document": doc
            }
        # If starting_index with 0 value not found
        elif doc_id not in unique_docs:
            unique_docs[doc_id] = {
                "metadata": meta,
                "document": doc
            }

    return list(unique_docs.values())



def generate(state: State):
    question = state.get("question", "")
    context_docs = state.get("context", [])

    docs_content = []
    for doc in context_docs:
        meta_str = "\n".join([f"{k}: {v}" for k, v in (doc.metadata or {}).items()])
        docs_content.append(f"Metadata:\n{meta_str}\n\nContent:\n{doc.page_content}")
    docs_content = "\n\n".join(docs_content)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Use only the provided context and metadata (username, due_date, is_tax_related, "
         "is_payment, etc.) carefully. "
         "If the information is insufficient, ask a clarifying question. "
         "Output must be ONLY the answer in a few sentences."),
        ("human", "Question: {question}\n\nContext:\n{context}")
    ])

    messages = prompt.invoke({"question": question, "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}


