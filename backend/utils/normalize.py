from services.db import DBService
from services.embeddings import Similarity
import numpy as np

db = DBService()
similarity_service = Similarity()

def normalize(data):
        """
            Normalize Vector Score and Keyword Score
        """
        if not data:
            return []
        arr = np.array(data, dtype=float)

        # Case 1: cosine similarity (Scaling normalization)
        if np.min(arr) >= -1 and np.max(arr) <= 1:
            return ((arr + 1) / 2).tolist()

        # Case 2: keyword / BM25 scores (min-max normalization)
        min_val, max_val = np.min(arr), np.max(arr)
        if min_val == max_val:  # avoid division by zero
            return [1.0] * len(arr)
        
        return ((arr - min_val) / (max_val - min_val)).tolist()

def calculate_hybrid(user_id,query,start_date,end_date,limit=1):
    embedding_input=similarity_service.encode(query)
    query_embedding=embedding_input.tolist() if hasattr(embedding_input, "tolist") else list(embedding_input)
    vector_results, keyword_results = db.get_tasks_by_user_id_and_title(query,query_embedding,user_id,start_date)

    combined_results = {}
    if vector_results:
        for doc in vector_results:
            doc_id = str(doc.get('_id'))
            doc.pop("embedding_vector", None)
            combined_results[doc_id] = {
                'vector_score': doc['score'],
                'keyword_score': 0.0,
                'document': {k: str(v) if k == '_id' else v for k, v in doc.items()}
            }

        # Process keyword results
        for doc in keyword_results:
            doc_id = str(doc.get('_id'))
            doc.pop("embedding_vector", None)
            if doc_id in combined_results:
                combined_results[doc_id]['keyword_score'] = doc['score']
            else:
                combined_results[doc_id] = {
                    'vector_score': 0.0,
                    'keyword_score': doc['score'],
                    'document': {k: str(v) if k == '_id' else v for k, v in doc.items()}
                }

        all_vector_scores = [item['vector_score'] for item in combined_results.values()]
        all_keyword_scores = [item['keyword_score'] for item in combined_results.values()]

        # Normalize scores
        norm_vector_scores = normalize(all_vector_scores)
        norm_keyword_scores = normalize(all_keyword_scores)

        alpha = 0.5
        for (doc_id, item), norm_v, norm_k in zip(combined_results.items(), norm_vector_scores, norm_keyword_scores):
            item['hybrid_score'] = alpha * norm_v + (1 - alpha) * norm_k
            item['document']['hybrid_score'] = item['hybrid_score']
            item['document'].pop('embeddings', None)

        # Sort by Hybrid Score
        ranked_results = sorted(combined_results.values(), key=lambda x: x['hybrid_score'], reverse=True)

        return [item['document'] for item in ranked_results[:limit]]