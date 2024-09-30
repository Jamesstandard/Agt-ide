from hashlib import md5
from typing import List, Optional, Dict, Any
import json

try:
    import lancedb
    import pyarrow as pa
    from lancedb.rerankers import Reranker
except ImportError:
    raise ImportError("`lancedb` not installed.")

from phi.document import Document
from phi.embedder import Embedder
from phi.embedder.openai import OpenAIEmbedder
from phi.vectordb.base import VectorDb
from phi.vectordb.distance import Distance
from phi.utils.log import logger


class LanceDb(VectorDb):
    def __init__(
        self,
        embedder: Embedder = OpenAIEmbedder(),
        distance: Distance = Distance.cosine,
        connection: Optional[lancedb.db.LanceTable] = None,
        uri: Optional[str] = "/tmp/lancedb",
        table_name: Optional[str] = "phi",
        nprobes: Optional[int] = None,
        query_type: Optional[str] = "vector",
        reranker: Optional[Reranker] = None,
    ):
        # Embedder for embedding the document contents
        self.embedder: Embedder = embedder
        self.dimensions: Optional[int] = self.embedder.dimensions

        # Distance metric
        self.distance: Distance = distance

        # Connection to lancedb table, can also be provided to use an existing connection
        self.uri = uri
        self.client = lancedb.connect(self.uri)
        self.nprobes = nprobes

        if connection:
            if not isinstance(connection, lancedb.db.LanceTable):
                raise ValueError(
                    "connection should be an instance of lancedb.db.LanceTable, ",
                    f"got {type(connection)}",
                )
            self.connection = connection
            self.table_name = self.connection.name
            self._vector_col = self.connection.schema.names[0]
            self._id = self.tbl.schema.names[1]  # type: ignore

        else:
            self.table_name = table_name
            self.connection = self._init_table()

        # Lancedb kwargs
        self.query_type = query_type
        self.reranker = reranker

        self.fts_index_exists = False

    def create(self) -> None:
        """Create the table if it does not exist."""
        if not self.exists():
            self.connection = self._init_table()  # Connection update is needed

    def _init_table(self) -> lancedb.db.LanceTable:
        self._id = "id"
        self._vector_col = "vector"
        schema = pa.schema(
            [
                pa.field(
                    self._vector_col,
                    pa.list_(
                        pa.float32(),
                        len(self.embedder.get_embedding("test")),  # type: ignore
                    ),
                ),
                pa.field(self._id, pa.string()),
                pa.field("payload", pa.string()),
            ]
        )

        logger.info(f"Creating table: {self.table_name}")
        tbl = self.client.create_table(self.table_name, schema=schema, mode="overwrite")
        return tbl

    def doc_exists(self, document: Document) -> bool:
        """
        Validating if the document exists or not

        Args:
            document (Document): Document to validate
        """
        if self.client:
            cleaned_content = document.content.replace("\x00", "\ufffd")
            doc_id = md5(cleaned_content.encode()).hexdigest()
            result = self.connection.search().where(f"{self._id}='{doc_id}'").to_arrow()
            return len(result) > 0
        return False

    def insert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """
        Insert documents into the database.

        Args:
            documents (List[Document]): List of documents to insert
            filters (Optional[Dict[str, Any]]): Filters to apply while inserting documents
        """
        logger.debug(f"Inserting {len(documents)} documents")
        data = []
        for document in documents:
            document.embed(embedder=self.embedder)
            cleaned_content = document.content.replace("\x00", "\ufffd")
            doc_id = str(md5(cleaned_content.encode()).hexdigest())
            payload = {
                "name": document.name,
                "meta_data": document.meta_data,
                "content": cleaned_content,
                "usage": document.usage,
            }
            data.append(
                {
                    "id": doc_id,
                    "vector": document.embedding,
                    "payload": json.dumps(payload),
                }
            )
            logger.debug(f"Inserted document: {document.name} ({document.meta_data})")

        self.connection.add(data)
        logger.debug(f"Upsert {len(data)} documents")

    def upsert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """
        Upsert documents into the database.

        Args:
            documents (List[Document]): List of documents to upsert
            filters (Optional[Dict[str, Any]]): Filters to apply while upserting
        """
        logger.debug("Redirecting the request to insert")
        self.insert(documents)

    def search(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        if self.query_type == "vector":
            return self.vector_search(query, limit)
        elif self.query_type == "hybrid":
            return self.hybrid_search(query, limit)
        elif self.query_type == "fts":
            return self.keyword_search(query, limit)
        else:
            logger.error(f"Invalid query type: {self.query_type} Supported query types: ['vector', 'hybrid', 'fts']")
            return []

    def vector_search(self, query: str, limit: int = 5) -> List[Document]:
        query_embedding = self.embedder.get_embedding(query)
        if query_embedding is None:
            logger.error(f"Error getting embedding for Query: {query}")
            return []

        results = self.connection.search(
            query=query_embedding,
            vector_column_name=self._vector_col,
        ).limit(limit)
        if self.nprobes:
            results.nprobes(self.nprobes)
        if self.reranker:
            results.rerank(reranker=self.reranker)
        results = results.to_pandas()

        search_results = self._build_search_results(results)

        return search_results

    def hybrid_search(self, query: str, limit: int = 5) -> List[Document]:
        query_embedding = self.embedder.get_embedding(query)
        if query_embedding is None:
            logger.error(f"Error getting embedding for Query: {query}")
            return []

        if not self.fts_index_exists:
            self.connection.create_fts_index("payload", replace=True)
            self.fts_index_exists = True

        results = self.connection.search(
            query=(query_embedding, query),
            vector_column_name=self._vector_col,
            query_type="hybrid",
        ).limit(limit)
        if self.nprobes:
            results.nprobes(self.nprobes)
        if self.reranker:
            results.rerank(reranker=self.reranker)
        results = results.to_pandas()

        search_results = self._build_search_results(results)

        return search_results

    def keyword_search(self, query: str, limit: int = 5) -> List[Document]:
        if not self.fts_index_exists:
            self.connection.create_fts_index("payload", replace=True)
            self.fts_index_exists = True

        results = (
            self.connection.search(
                query=query,
                query_type="fts",
            )
            .limit(limit)
            .to_pandas()
        )

        search_results = self._build_search_results(results)

        return search_results

    def _build_search_results(self, results) -> List[Document]:  # TODO: typehint pandas?
        search_results: List[Document] = []
        try:
            for _, item in results.iterrows():
                payload = json.loads(item["payload"])
                search_results.append(
                    Document(
                        name=payload["name"],
                        meta_data=payload["meta_data"],
                        content=payload["content"],
                        embedder=self.embedder,
                        embedding=item["vector"],
                        usage=payload["usage"],
                    )
                )

        except Exception as e:
            logger.error(f"Error building search results: {e}")

        return search_results

    def delete(self) -> None:
        if self.exists():
            logger.debug(f"Deleting collection: {self.table_name}")
            self.client.drop_table(self.table_name)

    def exists(self) -> bool:
        if self.client:
            if self.table_name in self.client.table_names():
                return True
        return False

    def get_count(self) -> int:
        if self.exists():
            return self.client.table(self.table_name).count_rows()
        return 0

    def optimize(self) -> None:
        pass

    def clear(self) -> bool:
        return False

    def name_exists(self, name: str) -> bool:
        raise NotImplementedError
