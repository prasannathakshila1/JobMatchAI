import numpy as np
from typing import List, Tuple, Optional
from app.ml.embeddings import embedding_engine
from app.ml.skill_extractor import skill_extractor
import logging

logger = logging.getLogger(__name__)


class SimilarityEngine:
    """
    Computes similarity between resume and job description.
    Uses both embedding cosine similarity and skill overlap.
    """

    # Weight mix for final score
    EMBEDDING_WEIGHT = 0.65    # Semantic similarity
    SKILL_WEIGHT     = 0.35    # Exact skill overlap

    def compute_match(self, resume_text: str, jd_text: str) -> dict:
        """
        Compute match score between one resume and one job description.
        Returns score 0–100 with full breakdown.
        """
        if not resume_text or not jd_text:
            return {"score": 0, "error": "Empty input text"}

        # 1. Embedding similarity
        emb_score = self._embedding_similarity(resume_text, jd_text)

        # 2. Skill overlap
        skill_result = self._skill_overlap(resume_text, jd_text)

        # 3. Weighted final score
        final_score = (
            emb_score * self.EMBEDDING_WEIGHT +
            skill_result["overlap_score"] * self.SKILL_WEIGHT
        )
        final_score = round(min(max(final_score, 0), 100), 1)

        # 4. Interview eligibility threshold
        eligible = final_score >= 65

        return {
            "score": final_score,
            "embedding_score": round(emb_score, 1),
            "skill_overlap_score": round(skill_result["overlap_score"], 1),
            "matched_skills": skill_result["matched"],
            "missing_skills": skill_result["missing"],
            "resume_skills": skill_result["resume_skills"],
            "jd_skills": skill_result["jd_skills"],
            "interview_eligible": eligible,
            "selection_probability": self._to_probability(final_score),
            "eligibility_label": "Interview Eligible ✅" if eligible else "Below Threshold ❌",
        }

    def rank_resumes(
        self,
        jd_text: str,
        resumes: List[dict],   # Each: {id, text, filename}
        top_n: int = 20,
    ) -> List[dict]:
        """
        Rank multiple resumes against one job description.
        Returns sorted list with scores.
        """
        if not jd_text or not resumes:
            return []

        results = []

        # Batch encode all resume texts + JD together for speed
        all_texts = [jd_text] + [r.get("text", "") for r in resumes]
        try:
            embeddings = embedding_engine.encode(all_texts)
            jd_embedding = embeddings[0]
            resume_embeddings = embeddings[1:]
            use_embeddings = True
        except Exception as e:
            logger.warning(f"Batch embedding failed, falling back: {e}")
            use_embeddings = False

        jd_skills = skill_extractor.extract(jd_text)

        for i, resume in enumerate(resumes):
            resume_text = resume.get("text", "")
            if not resume_text:
                continue

            # Embedding score
            if use_embeddings:
                emb_score = float(
                    np.dot(jd_embedding, resume_embeddings[i]) * 100
                )
            else:
                emb_score = self._embedding_similarity(resume_text, jd_text)

            # Skill overlap
            skill_result = self._skill_overlap(resume_text, jd_text, jd_skills=jd_skills)

            final_score = (
                emb_score * self.EMBEDDING_WEIGHT +
                skill_result["overlap_score"] * self.SKILL_WEIGHT
            )
            final_score = round(min(max(final_score, 0), 100), 1)

            results.append({
                "resume_id": resume.get("id"),
                "filename": resume.get("filename", "Unknown"),
                "candidate_name": resume.get("candidate_name", ""),
                "score": final_score,
                "embedding_score": round(emb_score, 1),
                "skill_overlap_score": round(skill_result["overlap_score"], 1),
                "matched_skills": skill_result["matched"],
                "missing_skills": skill_result["missing"],
                "interview_eligible": final_score >= 65,
                "selection_probability": self._to_probability(final_score),
            })

        # Sort by score descending, assign rank
        results.sort(key=lambda x: x["score"], reverse=True)
        for rank, item in enumerate(results[:top_n], start=1):
            item["rank"] = rank

        return results[:top_n]

    # ── Internal helpers ─────────────────────────────────────────

    def _embedding_similarity(self, text_a: str, text_b: str) -> float:
        """Cosine similarity between two texts scaled to 0–100."""
        try:
            embs = embedding_engine.encode([text_a, text_b])
            cosine = float(np.dot(embs[0], embs[1]))   # Already normalized
            return round(cosine * 100, 2)
        except Exception as e:
            logger.warning(f"Embedding similarity failed: {e}")
            return self._tfidf_fallback(text_a, text_b)

    def _tfidf_fallback(self, text_a: str, text_b: str) -> float:
        """TF-IDF cosine similarity fallback (no model needed)."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            vec = TfidfVectorizer(stop_words="english", max_features=5000)
            matrix = vec.fit_transform([text_a, text_b])
            score = cosine_similarity(matrix[0], matrix[1])[0][0]
            return round(float(score) * 100, 2)
        except Exception:
            return 0.0

    def _skill_overlap(
        self,
        resume_text: str,
        jd_text: str,
        jd_skills: Optional[List[str]] = None,
    ) -> dict:
        """Compute skill overlap score and lists."""
        resume_skills = set(skill_extractor.extract(resume_text))
        if jd_skills is None:
            jd_skills = skill_extractor.extract(jd_text)
        jd_skills_set = set(jd_skills)

        if not jd_skills_set:
            return {
                "overlap_score": 50.0,
                "matched": [],
                "missing": [],
                "resume_skills": list(resume_skills),
                "jd_skills": list(jd_skills_set),
            }

        matched = list(resume_skills & jd_skills_set)
        missing = list(jd_skills_set - resume_skills)
        overlap_score = (len(matched) / len(jd_skills_set)) * 100

        return {
            "overlap_score": round(overlap_score, 2),
            "matched": matched,
            "missing": missing,
            "resume_skills": list(resume_skills),
            "jd_skills": list(jd_skills_set),
        }

    def _to_probability(self, score: float) -> str:
        """Convert score to human-readable probability label."""
        if score >= 85:
            return "Very High (85–100%)"
        elif score >= 70:
            return "High (70–84%)"
        elif score >= 55:
            return "Medium (55–69%)"
        elif score >= 40:
            return "Low (40–54%)"
        else:
            return "Very Low (<40%)"


similarity_engine = SimilarityEngine()