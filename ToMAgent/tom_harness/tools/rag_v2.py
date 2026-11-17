"""RAG v4 Engine — unified-taxonomy semantic routing across a merged KB.

Pipeline per query:
  1. UnifiedQueryTagger -> 1-3 unified category labels (cached).
  2. Candidate pool: KB entries whose `unified_categories` overlap with the labels.
  3. Vector search + keyword rerank inside the pool.

Exported facade: RAGv2Engine (same interface as before for backward compat).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = str(Path(__file__).resolve().parent / "rag_v2_data")
_DEFAULT_INDEX_DIR = str(Path(__file__).resolve().parent / "rag_v2_index")


# ── UnifiedQueryTagger ─────────────────────────────────────────────────────

_TAGGER_PROMPT = """You are a Theory-of-Mind (ToM) task classifier.

Given a ToM question (story + question + options), choose the 1-3 most relevant categories from the unified taxonomy below.

UNIFIED TAXONOMY ({n} categories):

{categories_block}

=== Reference examples (one per category) ===

{examples_block}

=== Query to classify ===
Story: {story}
Question: {question}
Options:
{options_block}

Output ONLY a JSON array of 1-3 category names, ordered by relevance (most relevant first). Use names EXACTLY as listed above. No markdown, no commentary.

Example: ["False Belief Task", "See-Know"]
"""


def _query_hash(story: str, question: str, options: Dict[str, str]) -> str:
    payload = json.dumps(
        {"story": story, "question": question, "options": options},
        ensure_ascii=False, sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_categories_block(categories: List[dict]) -> str:
    return "\n".join(
        f"{i}. {c['name']} — {c['description']}"
        for i, c in enumerate(categories, 1)
    )


def _build_examples_block(categories: List[dict], max_story_chars: int = 200) -> str:
    blocks = []
    for c in categories:
        ex = c.get("example")
        if not ex:
            continue
        story = ex.get("story", "")[:max_story_chars]
        q = ex.get("question", "")
        blocks.append(f"[{c['name']}]\n  Story: {story}\n  Q: {q}")
    return "\n\n".join(blocks)


class UnifiedQueryTagger:
    """LLM-based query tagger over the unified 43-category taxonomy."""

    def __init__(
        self,
        taxonomy_path: str,
        cache_path: str,
        model_name: str = "qwen-turbo",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        use_cache: bool = True,
    ):
        self.taxonomy_path = Path(taxonomy_path)
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self.use_cache = use_cache

        with open(self.taxonomy_path) as f:
            tax = json.load(f)
        self.categories = tax["categories"]
        self.valid_names = {c["name"] for c in self.categories}

        self._categories_block = _build_categories_block(self.categories)
        self._examples_block = _build_examples_block(self.categories)

        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("HELPER_API_KEY") or ""
        self.api_base = api_base or os.getenv("OPENAI_API_BASE") or os.getenv("HELPER_API_BASE") or ""
        if not self.api_key or not self.api_base:
            raise ValueError(
                "Tagger requires API key/base. Set OPENAI_API_KEY+OPENAI_API_BASE "
                "or HELPER_API_KEY+HELPER_API_BASE env vars."
            )

        self._cache: Dict[str, List[str]] = {}
        self._cache_lock = threading.Lock()
        if self.use_cache:
            self._load_cache()

    def _load_cache(self):
        if not self.cache_path.exists():
            return
        with open(self.cache_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    self._cache[rec["hash"]] = rec["labels"]
                except Exception:
                    continue
        logger.info("[UnifiedQueryTagger] Loaded %d cached entries.", len(self._cache))

    def _write_cache(self, h: str, labels: List[str]):
        with self._cache_lock:
            self._cache[h] = list(labels)
            with open(self.cache_path, "a", encoding="utf-8") as f:
                json.dump({"hash": h, "labels": labels}, f, ensure_ascii=False)
                f.write("\n")

    def _build_prompt(self, story: str, question: str, options: Dict[str, str]) -> str:
        options_block = "\n".join(f"  {k}: {v}" for k, v in options.items() if v)
        return _TAGGER_PROMPT.format(
            n=len(self.categories),
            categories_block=self._categories_block,
            examples_block=self._examples_block,
            story=story,
            question=question,
            options_block=options_block,
        )

    def _parse_response(self, text: str) -> Optional[List[str]]:
        if not text:
            return None
        import re
        s = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
        if s.startswith("```"):
            parts = s.split("```", 2)
            if len(parts) >= 2:
                s = parts[1]
                if s.startswith("json"):
                    s = s[4:]
                s = s.strip("` \n")
        i = s.find("[")
        j = s.rfind("]")
        if i == -1 or j == -1 or j <= i:
            return None
        try:
            arr = json.loads(s[i: j + 1])
        except Exception:
            return None
        if not isinstance(arr, list):
            return None
        labels = [str(x).strip() for x in arr if x]
        labels = [la for la in labels if la in self.valid_names]
        return labels[:3] if labels else None

    def tag(self, story: str, question: str, options: Dict[str, str]) -> List[str]:
        h = _query_hash(story, question, options)
        if self.use_cache:
            with self._cache_lock:
                if h in self._cache:
                    return list(self._cache[h])

        prompt = self._build_prompt(story, question, options)

        import requests as _requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "temperature": 0,
            "max_tokens": 256,
            "messages": [
                {"role": "system", "content": "You are a precise classifier that responds in strict JSON."},
                {"role": "user", "content": prompt},
            ],
        }
        url = f"{self.api_base.rstrip('/')}/chat/completions"

        last_err = None
        for attempt in range(3):
            try:
                resp = _requests.post(url, headers=headers, json=payload, timeout=30)
                resp.raise_for_status()
                raw = resp.json()["choices"][0]["message"].get("content", "")
                parsed = self._parse_response(raw)
                if parsed:
                    self._write_cache(h, parsed)
                    return parsed
                last_err = f"parse failed; raw={raw[:200] if raw else ''}"
            except Exception as e:
                last_err = str(e)
                if attempt < 2:
                    time.sleep(2 ** attempt)
                continue

        logger.warning("[UnifiedQueryTagger] tagging failed for hash %s: %s", h[:8], last_err)
        self._write_cache(h, [])
        return []


# ── ToMRAGv4 core ──────────────────────────────────────────────────────────

STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'can', 'and', 'or', 'but', 'not',
    'no', 'yes', 'what', 'who', 'where', 'when', 'why', 'how', 'which',
    'that', 'this', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
    'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his',
    'her', 'its', 'our', 'their', 'of', 'in', 'on', 'at', 'to', 'for',
    'from', 'with', 'by', 'as', 'if', 'then', 'so', 'than', 'about',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further',
    'once', 'here', 'there', 'all', 'each', 'every', 'both', 'few',
    'more', 'most', 'other', 'some', 'such', 'only', 'own', 'same',
    'too', 'very', 'just', 'now', 'also', 'because', 'while',
}


class ToMRAGv4:
    """Core RAG engine: unified-taxonomy routing + FAISS + keyword rerank."""

    def __init__(
        self,
        data_dir: str,
        index_dir: str,
        model_name: str,
        kb_filename: str = "merged_kb_unified.jsonl",
        tagger: Optional[UnifiedQueryTagger] = None,
    ):
        self.data_dir = Path(data_dir)
        self.kb_filename = kb_filename
        self.index_dir = Path(index_dir) / Path(kb_filename).stem
        self.index_dir.mkdir(parents=True, exist_ok=True)

        from langchain_community.embeddings import HuggingFaceEmbeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
        )

        self.store = None
        self.loaded = False
        self.tagger = tagger

        self.entries_by_id: Dict[str, Dict] = {}
        self.ids_by_category: Dict[str, List[str]] = {}

    def _load_kb(self, file_path: Path) -> list:
        from langchain_core.documents import Document

        documents: list = []
        self.entries_by_id.clear()
        self.ids_by_category.clear()
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                eid = r["id"]
                text = r.get("text") or r.get("rule_en") or r.get("content") or ""
                unified = r.get("unified_categories", [])
                if not text or not unified:
                    continue
                self.entries_by_id[eid] = r
                for cat in unified:
                    self.ids_by_category.setdefault(cat, []).append(eid)
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "id": eid,
                            "source": r.get("source", "unknown"),
                            "title": r.get("title", ""),
                        },
                    )
                )
        return documents

    def build_index(self, force_rebuild: bool = False):
        from langchain_community.vectorstores import FAISS

        jsonl_file = self.data_dir / self.kb_filename
        if not jsonl_file.exists():
            logger.warning("[ToMRAGv4] data file %s not found", jsonl_file)
            return

        documents = self._load_kb(jsonl_file)
        index_path = self.index_dir / "store"

        if index_path.exists() and not force_rebuild:
            logger.info("[ToMRAGv4] Loading existing index from %s", index_path)
            self.store = FAISS.load_local(
                str(index_path), self.embeddings,
                allow_dangerous_deserialization=True,
            )
            self.loaded = True
            return

        logger.info("[ToMRAGv4] Embedding %d entries ...", len(documents))
        texts = [d.page_content for d in documents]
        metadatas = [d.metadata for d in documents]

        batch_size = 32
        all_emb = []
        for i in range(0, len(texts), batch_size):
            all_emb.extend(self.embeddings.embed_documents(texts[i: i + batch_size]))

        self.store = FAISS.from_embeddings(
            text_embeddings=list(zip(texts, all_emb)),
            embedding=self.embeddings,
            metadatas=metadatas,
        )
        self.store.save_local(str(index_path))
        logger.info("[ToMRAGv4] Saved index to %s", index_path)
        self.loaded = True

    def _extract_keywords(self, text: str) -> Set[str]:
        words = text.lower().split()
        return {w for w in words if w not in STOPWORDS and len(w) > 2}

    def _rerank_by_keywords(self, results: List[Dict], query: str, top_k: int) -> List[Dict]:
        qkw = self._extract_keywords(query)
        if not qkw:
            return results[:top_k]
        scored = []
        for r in results:
            ckw = self._extract_keywords(r["content"])
            scored.append((len(qkw & ckw), r))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [r for _, r in scored[:top_k]]

    def search(
        self,
        query: str,
        top_k: int = 3,
        story: str = "",
        question: str = "",
        options: Optional[Dict[str, str]] = None,
    ) -> List[Dict]:
        if not self.loaded:
            raise RuntimeError("Index not built. Call build_index() first.")

        options = options or {}

        if self.tagger is not None:
            labels = self.tagger.tag(story, question or query, options)
        else:
            labels = []

        if labels:
            candidate_ids: Set[str] = set()
            for cat in labels:
                for eid in self.ids_by_category.get(cat, []):
                    candidate_ids.add(eid)
            if not candidate_ids:
                candidate_ids = None
        else:
            candidate_ids = None

        fetch_k = max(top_k * 5, 30)
        docs = self.store.similarity_search(query, k=fetch_k)

        results: List[Dict] = []
        for doc in docs:
            eid = doc.metadata.get("id", "")
            if candidate_ids is not None and eid not in candidate_ids:
                continue
            entry = self.entries_by_id.get(eid, {})
            results.append({
                "content": doc.page_content,
                "source": entry.get("source", ""),
                "category": (entry.get("unified_categories") or [""])[0],
                "title": entry.get("title", ""),
                "id": eid,
            })
            if len(results) >= top_k * 3:
                break

        if not results and candidate_ids is not None:
            for doc in docs:
                entry = self.entries_by_id.get(doc.metadata.get("id", ""), {})
                results.append({
                    "content": doc.page_content,
                    "source": entry.get("source", ""),
                    "category": (entry.get("unified_categories") or [""])[0],
                    "title": entry.get("title", ""),
                    "id": doc.metadata.get("id", ""),
                })
                if len(results) >= top_k * 3:
                    break

        return self._rerank_by_keywords(results, query, top_k=top_k)

    def format_context(self, results: List[Dict], max_length: int = 1500) -> str:
        parts: List[str] = []
        total = 0
        for i, r in enumerate(results, 1):
            piece = f"[{i}] {r['content']}"
            if total + len(piece) > max_length:
                break
            parts.append(piece)
            total += len(piece)
        return "\n".join(parts)


# ── CategoryClassifier (deprecated stub for backward compat) ───────────────

@dataclass
class CategoryClassifier:
    """Deprecated: kept only so existing imports don't break."""
    api_base: str = ""
    api_key: str = ""
    model: str = "qwen-turbo"
    max_retries: int = 3
    timeout: float = 30.0

    def classify(self, question: str, story: str = "") -> str | None:
        return None


# ── RAGv2Engine facade (backward-compatible interface) ─────────────────────

@dataclass
class RAGv2Engine:
    """Facade wrapping ToMRAGv4 for use by HarnessRuntime.

    Keeps the same constructor/method signatures so runtime.py and example
    scripts require minimal changes.
    """

    data_dir: str = _DEFAULT_DATA_DIR
    index_dir: str = _DEFAULT_INDEX_DIR
    model_name: str = "model/bge-m3"
    use_category_filter: bool = True  # ignored, kept for compat
    classifier: CategoryClassifier | None = None  # used only to extract api creds
    tagger_model: str = ""

    _backend: Any = field(default=None, init=False, repr=False)
    _ready: bool = field(default=False, init=False, repr=False)

    def build_index(self, force_rebuild: bool = False, num_samples: int = -1) -> None:
        data_path = Path(self.data_dir)
        if not data_path.exists():
            logger.warning("[RAG] data_dir %s does not exist — running in empty mode", data_path)
            return

        taxonomy_path = str(data_path / "unified_taxonomy_flat.json")
        cache_path = str(data_path / "cache" / "query_tags_unified.jsonl")

        tagger_model = self.tagger_model or (
            self.classifier.model if self.classifier else "qwen-turbo"
        )
        api_key = (self.classifier.api_key if self.classifier else None) or None
        api_base = (self.classifier.api_base if self.classifier else None) or None

        tagger: UnifiedQueryTagger | None = None
        if Path(taxonomy_path).exists():
            try:
                tagger = UnifiedQueryTagger(
                    taxonomy_path=taxonomy_path,
                    cache_path=cache_path,
                    model_name=tagger_model,
                    api_key=api_key,
                    api_base=api_base,
                    use_cache=True,
                )
            except Exception as e:
                logger.warning("[RAG] UnifiedQueryTagger init failed: %s — running without tagger", e)
        else:
            logger.warning("[RAG] taxonomy file not found at %s — running without tagger", taxonomy_path)

        self._backend = ToMRAGv4(
            data_dir=self.data_dir,
            index_dir=self.index_dir,
            model_name=self.model_name,
            tagger=tagger,
        )
        self._backend.build_index(force_rebuild=force_rebuild)
        self._ready = self._backend.loaded

        if self._ready:
            logger.info("[RAG] Index ready — %d documents", self._backend.store.index.ntotal)

    def retrieve(
        self,
        query: str,
        category: str | None = None,
        top_k: int = 5,
        story: str = "",
        options: dict[str, str] | None = None,
    ) -> str:
        if not self._ready:
            return ""
        results = self._backend.search(
            query=query, top_k=top_k, story=story,
            question=query, options=options,
        )
        ctx = self._backend.format_context(results)
        if ctx:
            logger.debug("[RAG] Retrieved %d entries", len(results))
        return ctx

    def size(self) -> int:
        if not self._ready or self._backend.store is None:
            return 0
        return self._backend.store.index.ntotal
