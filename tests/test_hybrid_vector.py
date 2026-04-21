from langchain_core.documents import Document
from dao.vector.hybrid_vector import HybridVectorRepository


class TestRrfMerge:
    """Test the RRF merge algorithm without requiring ChromaDB or embeddings."""

    def _make_doc(self, text, source="test"):
        return Document(page_content=text, metadata={"source": source})

    def _call_rrf(self, semantic, bm25, k=6, rrf_k=60):
        repo = HybridVectorRepository.__new__(HybridVectorRepository)
        return repo._rrf_merge(semantic, bm25, k=k, rrf_k=rrf_k)

    def test_merge_disjoint_lists(self):
        sem = [self._make_doc("semantic doc 1"), self._make_doc("semantic doc 2")]
        bm25 = [self._make_doc("bm25 doc 1"), self._make_doc("bm25 doc 2")]

        result = self._call_rrf(sem, bm25, k=4)
        texts = [d.page_content for d in result]

        assert len(result) == 4
        assert "semantic doc 1" in texts
        assert "bm25 doc 1" in texts

    def test_merge_overlapping_lists(self):
        shared = self._make_doc("shared document with enough text to be unique key")
        sem = [shared, self._make_doc("only semantic")]
        bm25 = [shared, self._make_doc("only bm25")]

        result = self._call_rrf(sem, bm25, k=3)
        texts = [d.page_content for d in result]

        # Shared doc should rank first (appears in both lists)
        assert result[0].page_content == "shared document with enough text to be unique key"
        assert len(result) == 3

    def test_merge_empty_lists(self):
        result = self._call_rrf([], [], k=6)
        assert result == []

    def test_merge_one_empty_list(self):
        sem = [self._make_doc("doc 1"), self._make_doc("doc 2")]
        result = self._call_rrf(sem, [], k=6)
        assert len(result) == 2

    def test_k_limits_results(self):
        sem = [self._make_doc(f"sem {i}") for i in range(10)]
        bm25 = [self._make_doc(f"bm25 {i}") for i in range(10)]
        result = self._call_rrf(sem, bm25, k=3)
        assert len(result) == 3

    def test_higher_ranked_docs_score_higher(self):
        sem = [self._make_doc("first"), self._make_doc("second"), self._make_doc("third")]
        result = self._call_rrf(sem, [], k=3, rrf_k=60)

        # First doc should remain first after RRF
        assert result[0].page_content == "first"


class TestHybridVectorSaveValidation:
    """Test save method input validation without external dependencies."""

    def _make_repo(self):
        repo = HybridVectorRepository.__new__(HybridVectorRepository)
        repo._bm25_index = None
        repo._bm25_corpus = []
        return repo

    def test_save_empty_text_returns_early(self):
        repo = self._make_repo()
        # Should not raise - just return
        repo.save("", "https://example.com")
        repo.save("   ", "https://example.com")

    def test_save_none_text_returns_early(self):
        repo = self._make_repo()
        repo.save(None, "https://example.com")

    def test_saveAll_empty_list_returns_early(self):
        repo = self._make_repo()
        repo.saveAll([], "https://example.com")

    def test_saveAll_none_returns_early(self):
        repo = self._make_repo()
        repo.saveAll(None, "https://example.com")

    def test_chunk_size_constants(self):
        assert HybridVectorRepository.CHUNK_SIZE == 1900
        assert HybridVectorRepository.CHUNK_OVERLAP == 190
