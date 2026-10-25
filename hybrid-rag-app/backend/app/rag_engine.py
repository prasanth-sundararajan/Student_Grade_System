import os
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.retrievers import BM25Retriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from sentence_transformers import CrossEncoder
from app.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

class HybridRAGEngine:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        # Initialize VectorDB, BM25, and corpus references
        self.vector_store = None
        self.bm25_retriever = None
        self.documents_corpus = []
        
        # Initialize Neo4j Knowledge Graph connection
        try:
            self.graph = Neo4jGraph(
                url=NEO4J_URI,
                username=NEO4J_USERNAME,
                password=NEO4J_PASSWORD
            )
            print("Connected to Neo4j successfully.")
        except Exception as e:
            print(f"Neo4j connection warning: {e}")
            self.graph = None

    def process_document(self, file_path: str):
        """
        1. Loads PDF and splits into chunks (size 1500, overlap 200).
        2. Indexes chunks into FAISS VectorDB (saves locally) and BM25 Retriever.
        3. Extracts semantic entities & relationships using LLMGraphTransformer and loads into Neo4j.
        """
        loader = PyPDFLoader(file_path)
        raw_docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        docs = text_splitter.split_documents(raw_docs)
        
        self.documents_corpus.extend(docs)
        texts = [d.page_content for d in self.documents_corpus]

        # 1. Update/Initialize FAISS VectorDB & Save Locally
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(docs, self.embeddings)
        else:
            self.vector_store.add_documents(docs)
        
        os.makedirs("./faiss_index", exist_ok=True)
        self.vector_store.save_local("./faiss_index")

        # 2. Update/Initialize BM25 Keyword Retriever
        self.bm25_retriever = BM25Retriever.from_texts(texts)
        self.bm25_retriever.k = 4

        # 3. LLM Semantic Knowledge Graph Population (Neo4j)
        graph_status = "Skipped"
        if self.graph:
            try:
                print("Extracting semantic entities and relationships using LLMGraphTransformer...")
                llm_transformer = LLMGraphTransformer(llm=self.llm)
                
                graph_documents = llm_transformer.convert_to_graph_documents(docs)
                
                self.graph.add_graph_documents(
                    graph_documents,
                    baseEntityLabel=True,
                    include_source=True
                )
                graph_status = "Successfully populated semantic knowledge graph"
            except Exception as e:
                print(f"Graph ingestion error: {e}")
                graph_status = f"Error: {e}"

        return {
            "status": "success", 
            "chunks_indexed": len(docs), 
            "graph_status": graph_status,
            "message": f"Successfully processed and indexed {file_path}"
        }

    def reciprocal_rank_fusion(self, vector_results, bm25_results, k=60) -> List[Any]:
        fused_scores = {}
        doc_map = {}

        def add_scores(results):
            for rank, doc in enumerate(results):
                doc_text = doc.page_content
                doc_map[doc_text] = doc
                if doc_text not in fused_scores:
                    fused_scores[doc_text] = 0
                fused_scores[doc_text] += 1 / (k + rank + 1)

        add_scores(vector_results)
        add_scores(bm25_results)

        sorted_docs = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_map[doc_text] for doc_text, score in sorted_docs]

    def query(self, question: str) -> Dict[str, Any]:
        if not self.vector_store or not self.bm25_retriever:
            return {"answer": "Please upload and index a document first.", "sources": []}

        # 1. Retrieve from VectorDB (FAISS)
        vector_docs = self.vector_store.similarity_search(question, k=4)

        # 2. Retrieve from BM25 (Keyword)
        bm25_docs = self.bm25_retriever.invoke(question)

        # 3. Reciprocal Rank Fusion (RRF)
        fused_docs = self.reciprocal_rank_fusion(vector_docs, bm25_docs)

        # 4. Cross-Encoder Reranking
        pairs = [[question, doc.page_content] for doc in fused_docs]
        if pairs:
            scores = self.reranker.predict(pairs)
            scored_docs = sorted(zip(fused_docs, scores), key=lambda x: x[1], reverse=True)
            top_docs = [doc for doc, score in scored_docs[:3]]
        else:
            top_docs = fused_docs[:3]

        # 5. Semantic Knowledge Graph Context Retrieval (Neo4j)
        graph_context = ""
        if self.graph:
            try:
                keyword = question.split()[0] if question else "scheme"
                cypher_query = """
                MATCH (n)-[r]->(m)
                WHERE toLower(n.id) CONTAINS toLower($keyword) OR toLower(m.id) CONTAINS toLower($keyword)
                RETURN n.id AS source, type(r) AS relation, m.id AS target
                LIMIT 5
                """
                graph_data = self.graph.query(cypher_query, {"keyword": keyword})
                if graph_data:
                    graph_context = "\n".join([f"({row['source']}) -[:{row['relation']}]-> ({row['target']})" for row in graph_data])
            except Exception as e:
                print(f"Graph query warning: {e}")

        # 6. Format Context & Generate Answer via LLM
        context_text = "\n\n".join([doc.page_content for doc in top_docs])
        if graph_context:
            context_text += f"\n\nSemantic Knowledge Graph Triples:\n{graph_context}"

        prompt = f"""Answer the question accurately based on the provided context and graph relationships. If the answer is not in the context, state that you don't know.

Context:
{context_text}

Question: {question}
Answer:"""

        response = self.llm.invoke(prompt)
        return {
            "answer": response.content,
            "sources": [doc.page_content[:150] for doc in top_docs]
        }

rag_engine = HybridRAGEngine()