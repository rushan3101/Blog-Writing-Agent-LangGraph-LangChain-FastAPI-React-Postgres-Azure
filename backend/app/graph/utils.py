from typing import List
import os
import requests
import base64
import re
from app.core.config import settings

def _tavily_search(query: str, max_results) -> List[dict]:
    """
    Search Tavily API for relevant articles for a given query and return a list of dicts containing title, url, snippet, published_at, source of each result
    
    :param query: Query to search for relevant articles
    :type query: str
    :param max_results: Maximum number of results to return
    :return: List of dicts containing title, url, snippet, published_at, source of each result
    :rtype: List[dict]
    """
    if not os.getenv("TAVILY_API_KEY"):
        return []
    try:
        from langchain_tavily import TavilySearch  
        tool = TavilySearch(tavily_api_key=os.getenv("TAVILY_API_KEY"), max_results=max_results)
        results = tool.invoke({"query": query})["results"]
        out = []
        for r in results or []:
            out.append(
                {
                    "title": r.get("title") or "",
                    "url": r.get("url") or "",
                    "snippet": r.get("content") or r.get("snippet") or "",
                    "published_at": r.get("published_date") or r.get("published_at"),
                    "source": r.get("source"),
                }
            )
        return out
    except Exception as e:
        print(e)
        return []
    

def _puter_generate_image_bytes(prompt: str) -> bytes:
    """
    Generate image using Puter and return raw image bytes
    
    :param prompt: Prompt to send to the image model
    :type prompt: str
    :return: Bytes of the generated image
    :rtype: bytes
    """

    token = settings.PUTER_TOKEN
    model = settings.IMAGE

    if not token:
        raise RuntimeError("PUTER_TOKEN is not set.")

    payload = {
        "interface": "puter-image-generation",
        "driver": "ai-image",
        "method": "generate",
        "test_mode": False,
        "args": {
            "model": model,
            "prompt": prompt,
        },
        "auth_token": token,
    }

    response = requests.post(
        "https://api.puter.com/drivers/call",
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    result = response.json()

    if "result" not in result:
        raise RuntimeError(f"Unexpected response: {result}")

    data_uri = result["result"]

    if not data_uri.startswith("data:image"):
        raise RuntimeError(f"Expected image data URI, got: {data_uri[:100]}")

    try:
        _, image_b64 = data_uri.split(",", 1)
        return base64.b64decode(image_b64)
    except Exception as e:
        raise RuntimeError(f"Failed to decode image response: {e}")
    

def _safe_slug(title: str) -> str:
    """
    Generate a safe slug from a title
    
    :param title: Title
    :type title: str
    :return: Safe slug
    :rtype: str
    """
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"
