"""
Local RAG Retrieval Engine for RetailIQ
Retrieves authoritative retail rules and inventory policies from docs/retail_rules.md.
Uses Gemini Embeddings (gemini-embedding-001) when API key is provided,
with an instant local TF-IDF / cosine-similarity fallback for 100% offline/fast reliability.
Zero hosted vector databases.
"""

import os
import re
import json
import math
import numpy as np
from typing import List, Dict, Any, Optional

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
RULES_FILE = os.path.join(DOCS_DIR, "retail_rules.md")
EMBEDDINGS_CACHE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "policy_embeddings.json")

class PolicyRetriever:
    def __init__(self, rules_path: str = RULES_FILE):
        self.rules_path = rules_path
        self.chunks = []
        self.load_and_chunk_rules()
        self.vocab = {}
        self.chunk_vectors = []
        self._build_local_index()

    def load_and_chunk_rules(self):
        """Splits retail_rules.md into semantic sections."""
        if not os.path.exists(self.rules_path):
            return

        with open(self.rules_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by level 2 headings '## '
        sections = re.split(r'\n(?=## \d+\. )', content)
        for idx, sec in enumerate(sections):
            sec = sec.strip()
            if not sec:
                continue
            lines = sec.split("\n")
            title = lines[0].replace("#", "").strip()
            body = "\n".join(lines[1:]).strip()
            
            # Extract rule or section number if present
            match = re.search(r'(\d+)', title)
            sec_num = match.group(1) if match else str(idx + 1)

            self.chunks.append({
                "id": f"sec_{sec_num}",
                "section_number": sec_num,
                "title": title,
                "text": sec,
                "body": body,
                "citation": f"docs/retail_rules.md Section {sec_num} ({title})"
            })

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-zA-Z0-9_\-\$]+\b', text.lower())

    def _build_local_index(self):
        """Builds local TF-IDF vectors for deterministic, instant retrieval."""
        all_words = []
        doc_freq = {}
        total_docs = len(self.chunks)

        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk["text"]))
            for t in tokens:
                doc_freq[t] = doc_freq.get(t, 0) + 1

        # Vocabulary of terms appearing in at least 1 chunk
        self.vocab = {word: idx for idx, (word, freq) in enumerate(doc_freq.items())}
        vocab_size = len(self.vocab)

        self.chunk_vectors = []
        for chunk in self.chunks:
            tokens = self._tokenize(chunk["text"])
            vec = np.zeros(vocab_size)
            if not tokens:
                self.chunk_vectors.append(vec)
                continue
            
            token_counts = {}
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1
            
            for t, count in token_counts.items():
                if t in self.vocab:
                    tf = count / len(tokens)
                    idf = math.log((total_docs + 1) / (doc_freq[t] + 1)) + 1
                    vec[self.vocab[t]] = tf * idf
            
            # L2 normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            self.chunk_vectors.append(vec)

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant policy sections for a query.
        Returns matching chunks with citation, title, and body.
        """
        if not self.chunks:
            return []

        # Check for Gemini Embeddings if available and cached
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                gemini_res = self._retrieve_with_gemini(query, top_k, api_key)
                if gemini_res:
                    return gemini_res
            except Exception:
                pass # Gracefully fall back to local TF-IDF

        # Fast local TF-IDF vector retrieval
        tokens = self._tokenize(query)
        if not tokens:
            return [self.chunks[0]]

        q_vec = np.zeros(len(self.vocab))
        token_counts = {}
        for t in tokens:
            token_counts[t] = token_counts.get(t, 0) + 1

        for t, count in token_counts.items():
            if t in self.vocab:
                q_vec[self.vocab[t]] = count

        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scores = []
        for idx, c_vec in enumerate(self.chunk_vectors):
            score = float(np.dot(q_vec, c_vec))
            
            # Bonus matching for explicit keywords like 'stockout', 'overstock', 'reorder', 'spike', 'drop'
            q_lower = query.lower()
            if "stockout" in q_lower or "running out" in q_lower or "low stock" in q_lower:
                if "stock-out" in self.chunks[idx]["title"].lower() or "inventory metric" in self.chunks[idx]["title"].lower():
                    score += 0.35
            if "overstock" in q_lower or "excess" in q_lower:
                if "overstock" in self.chunks[idx]["title"].lower():
                    score += 0.40
            if "spike" in q_lower or "surge" in q_lower:
                if "spike" in self.chunks[idx]["title"].lower():
                    score += 0.40
            if "drop" in q_lower or "slow" in q_lower or "sluggish" in q_lower:
                if "drop" in self.chunks[idx]["title"].lower() or "slow-moving" in self.chunks[idx]["title"].lower():
                    score += 0.40
            if "reorder" in q_lower or "attention" in q_lower or "order" in q_lower:
                if "reorder" in self.chunks[idx]["text"].lower():
                    score += 0.25

            scores.append((score, self.chunks[idx]))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scores[:top_k]]

    def _retrieve_with_gemini(self, query: str, top_k: int, api_key: str) -> Optional[List[Dict[str, Any]]]:
        """Attempts retrieval using Gemini gemini-embedding-001 if online."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Embed query
            res = genai.embed_content(
                model="models/gemini-embedding-001",
                content=query,
                task_type="retrieval_query"
            )
            q_emb = np.array(res["embedding"])
            
            # If we don't have cached chunk embeddings, build them once
            cached_embs = self._load_or_create_gemini_embeddings(genai)
            if not cached_embs:
                return None

            scores = []
            for chunk, c_emb in zip(self.chunks, cached_embs):
                c_arr = np.array(c_emb)
                sim = float(np.dot(q_emb, c_arr) / (np.linalg.norm(q_emb) * np.linalg.norm(c_arr)))
                scores.append((sim, chunk))

            scores.sort(key=lambda x: x[0], reverse=True)
            return [c for sim, c in scores[:top_k]]
        except Exception:
            return None

    def _load_or_create_gemini_embeddings(self, genai) -> Optional[List[List[float]]]:
        """Loads cached embeddings from disk or computes them via Gemini Embeddings."""
        if os.path.exists(EMBEDDINGS_CACHE):
            try:
                with open(EMBEDDINGS_CACHE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # Compute embeddings
        embeddings = []
        try:
            for c in self.chunks:
                res = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=c["text"][:1000],
                    task_type="retrieval_document"
                )
                embeddings.append(res["embedding"])

            # Cache to disk
            os.makedirs(os.path.dirname(EMBEDDINGS_CACHE), exist_ok=True)
            with open(EMBEDDINGS_CACHE, "w", encoding="utf-8") as f:
                json.dump(embeddings, f)
            return embeddings
        except Exception:
            return None
