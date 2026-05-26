# import pydantic 


# class RAGChunkAndSrc(pydantic.BaseModel):
#     chunks: list[str]
#     source_id: str = None
    

# class RAGUpsertResult(pydantic.BaseModel):
#     ingested: int
    

# class RAGSearchResult(pydantic.BaseModel):
#     contexts: list[str]
#     sources:list[str]
    

# class RAGQueryResult(pydantic.BaseModel):
#     answer: str
#     sources: list[str]
#     num_contexts: int
    
    
    


from pydantic import BaseModel
from typing import List


# =====================================================
# PDF CHUNKING
# =====================================================

class RAGChunkAndSrc(BaseModel):
    chunks: List[str]
    source_id: str


# =====================================================
# UPSERT RESULT
# =====================================================

class RAGUpsertResult(BaseModel):
    ingested: int


# =====================================================
# VECTOR SEARCH RESULT
# =====================================================

class RAGSearchResult(BaseModel):
    contexts: List[str]
    sources: List[str]


# =====================================================
# FINAL QUERY RESULT
# =====================================================

class RAGQueryResult(BaseModel):
    answer: str
    sources: List[str]
    num_contexts: int