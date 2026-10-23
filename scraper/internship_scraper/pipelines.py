import hashlib
import logging
import re
from typing import Any, Dict, Union

from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)


def _getter(item):
    return lambda key: item.get(key, "") if isinstance(item, dict) else getattr(item, key, "")


class ContentDeduplicationPipeline:
    """
    Generates a conservative fallback SHA256 signature from company, title and country.
    The backend uses it to avoid storing the same offer twice.
    """

    def process_item(self, item: Union[Dict[str, Any], Any], spider) -> Union[Dict[str, Any], Any]:
        get_val = _getter(item)

        company = get_val("company")
        title = get_val("normalized_title") or get_val("title")
        country = get_val("country")

        raw_sig = f"{str(company).lower()}|{str(title).lower()}|{str(country).lower()}"
        clean_sig = re.sub(r"[^a-z0-9|]", "", raw_sig)
        fingerprint = hashlib.sha256(clean_sig.encode("utf-8")).hexdigest()

        if isinstance(item, dict):
            item["fingerprint"] = fingerprint
        else:
            item.fingerprint = fingerprint

        return item


class KeywordFilterPipeline:
    """
    Drops listings that are not relevant to AI / Data Science / ML / PFE and
    extracts known skills into required_skills for the ones that are kept.
    """

    TARGET_KEYWORDS = {
    # English
        "artificial intelligence", "ai", "machine learning", "deep learning",
        "data science", "data engineer", "data engineering", "nlp",
        "natural language processing", "computer vision", "llm", "pfe",
        "end of studies", "end-of-studies", "master thesis", "applied ai",
        "neural network", "neural networks", "reinforcement learning", "big data",
        "data intelligence",
        # French
        "intelligence artificielle", "ia", "apprentissage automatique",
        "apprentissage profond", "apprentissage statistique", "science des données",
        "sciences des données", "ingénieur données", "réseau de neurones",
        "réseaux de neurones", "vision par ordinateur",
        "traitement automatique des langues", "traitement du langage naturel",
        "stage de fin d'études",
    }

    SKILL_VOCABULARY = {
        "python", "pytorch", "tensorflow", "scikit-learn", "sql", "spark",
        "hadoop", "docker", "kubernetes", "aws", "gcp", "azure", "fastapi",
        "mlflow", "huggingface", "transformers", "opencv", "langchain",
    }

    def process_item(self, item: Union[Dict[str, Any], Any], spider) -> Union[Dict[str, Any], Any]:
        get_val = _getter(item)

        title = get_val("title")
        description = get_val("description")
        full_text = f"{title} {description}".lower()
        full_text = full_text.replace("’", "'")

        if not any(re.search(rf"\b{re.escape(k)}\b", full_text) for k in self.TARGET_KEYWORDS):
            raise DropItem(f"Not relevant: {str(title)[:60]}")

        extracted_skills = {
            skill for skill in self.SKILL_VOCABULARY
            if re.search(rf"(?<![\w-]){re.escape(skill)}(?![\w-])", full_text)
        }

        if isinstance(item, dict):
            item["required_skills"] = sorted(extracted_skills)
        else:
            item.required_skills = sorted(extracted_skills)

        return item