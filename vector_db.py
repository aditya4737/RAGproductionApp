# from qdrant_client import QdrantClient
# from qdrant_client.models import VectorParams, Distance, PointStruct


# class QdrantStorage:
#     def __init__(self, url="http://localhost:6333", collection="docs", dim=1536):
#         self.client = QdrantClient(url=url, timeout=30)
#         self.collection = collection

#         if not self.client.collection_exists(self.collection):
#             self.client.create_collection(
#                 collection_name=self.collection,
#                 vectors_config=VectorParams(
#                     size=dim,
#                     distance=Distance.COSINE
#                 ),
#             )

#     def upsert(self, ids, vectors, payloads):
#         points = [
#             PointStruct(
#                 id=ids[i],
#                 vector=vectors[i],
#                 payload=payloads[i]
#             )
#             for i in range(len(ids))
#         ]

#         self.client.upsert(
#             collection_name=self.collection,
#             points=points
#         )

#     def search(self, query_vector, top_k: int = 5):
#         results = self.client.search(
#             collection_name=self.collection,
#             query_vector=query_vector,
#             with_payload=True,
#             limit=top_k
#         )

#         contexts = []
#         sources = set()

#         for r in results:
#             payload = getattr(r, "payload", None) or {}

#             text = payload.get("text", "")
#             source = payload.get("source", "")

#             if text:
#                 contexts.append(text)

#             if source:
#                 sources.add(source)

#         return {
#             "contexts": contexts,
#             "sources": list(sources)
#         }


import os

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)


class QdrantStorage:

    def __init__(self):

        self.collection_name = "rag_collection"

        self.vector_size = 384

        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )

        self._create_collection_if_not_exists()

    # =====================================================
    # CREATE COLLECTION
    # =====================================================

    def _create_collection_if_not_exists(self):

        collections = self.client.get_collections().collections

        collection_names = [
            collection.name
            for collection in collections
        ]

        if self.collection_name not in collection_names:

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )

    # =====================================================
    # UPSERT
    # =====================================================

    def upsert(
        self,
        ids,
        vectors,
        payloads
    ):

        points = []

        for i in range(len(ids)):

            points.append(
                PointStruct(
                    id=ids[i],
                    vector=vectors[i],
                    payload=payloads[i]
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    # =====================================================
    # SEARCH
    # =====================================================

    def search(
        self,
        query_vector,
        top_k=5
    ):

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k
        )

        contexts = []
        sources = []

        for point in results.points:

            payload = point.payload

            contexts.append(
                payload.get("text", "")
            )

            sources.append(
                payload.get("source", "")
            )

        return {
            "contexts": contexts,
            "sources": sources
        }