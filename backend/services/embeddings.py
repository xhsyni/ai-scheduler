from sentence_transformers import SentenceTransformer
import numpy as np

class Similarity:
    def __init__(self):
        self.model_name = "thenlper/gte-large"
        self.model = SentenceTransformer(self.model_name)

    def encode(self, sentences):
        if isinstance(sentences, str):
            res = self.model.encode(sentences)
        else:
            res = self.model.encode(sentences)
        return np.array(res)

    def calculate(self, query, target):
        query_vector = np.array(self.model.encode(query))
        target_vectors = [np.array(self.model.encode(tar)) for tar in target ]

        cosine_similarity = [np.dot(query_vector, target_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(target_vector)
            ) for target_vector in target_vectors
        ]
        return cosine_similarity