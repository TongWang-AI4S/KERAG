"""NodeSearcher for searching nodes in the knowledge graph."""

import re
from typing import Dict, List, Optional, Any, Union

from .knowledge_manager import KnowledgeManager

class NodeSearcher:
    """Searcher for finding nodes based on text matching."""

    def __init__(self, knowledge_manager: KnowledgeManager):
        self.km = knowledge_manager
        # Cache for search results: (query_tuple, scope, max_results, whole_word, case_sensitive) -> results
        self._search_cache: Dict[tuple, Dict[str, Any]] = {}

    def _matches_query(self, text: str, q: str, whole_word: bool, case_sensitive: bool, use_regex: bool = False) -> bool:
        """Check if text matches the query string with given options."""
        if use_regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(q, text, flags=flags))
            except re.error:
                return False # Invalid regex, fallback to no match

        if not case_sensitive:
            text = text.lower()
            q = q.lower()

        if whole_word:
            # Use word boundary matching for whole word match
            pattern = r'\b' + re.escape(q) + r'\b'
            return bool(re.search(pattern, text, flags=0 if case_sensitive else re.IGNORECASE))
        return q in text

    def search(self, query: Union[str, List[str]], scope: str = "all", max_results: int = 50,
               whole_word: bool = False, case_sensitive: bool = False, use_regex: bool = False) -> Dict[str, Any]:
        """Search for nodes containing the query text(s).
        
        Args:
            query: Search query text or list of query texts
            scope: Search scope "all" | "title" | "content" | "label"
            max_results: Maximum number of results to return
            whole_word: Whether to match whole words only
            case_sensitive: Whether the search is case sensitive
            use_regex: Whether to treat query as a regular expression

        Returns:
            Dictionary containing search results
        """
        if not query:
            return {
                "error": {
                    "type": "invalid_query",
                    "message": "Search query cannot be empty"
                }
            }

        # Normalize query to list and then tuple for caching
        queries = [query] if isinstance(query, str) else query
        if not all(isinstance(q, str) for q in queries):
            return {"error": {"type": "invalid_query", "message": "Queries must be strings"}}

        query_key = (tuple(sorted(queries)), scope, max_results, whole_word, case_sensitive, use_regex)

        # Check cache
        if query_key in self._search_cache:
            return self._search_cache[query_key]

        results = []
        seen_ids = set()

        # Iterate through all nodes in KnowledgeManager
        for node_id in self.km.nodes:
            if len(results) >= max_results:
                break

            if node_id in seen_ids:
                continue

            node = self.km.get_node(node_id)
            if node is None:
                continue

            # Check if ANY query matches at least one field in the node (within scope)
            any_query_matched = False
            for q in queries:
                q_matched = False

                # Check title
                if scope in ["all", "title"] and node.get("node_type") == "section":
                    text_to_check = node.get("title", "")
                    if self._matches_query(text_to_check, q, whole_word, case_sensitive, use_regex):
                        q_matched = True

                # Check content
                if not q_matched and scope in ["all", "content"] and node.get("node_type") == "content":
                    text_to_check = node.get("content", "")
                    if self._matches_query(text_to_check, q, whole_word, case_sensitive, use_regex):
                        q_matched = True

                # Check label
                if not q_matched and scope in ["all", "label"]:
                    text_to_check = node.get("label", "")
                    if self._matches_query(text_to_check, q, whole_word, case_sensitive, use_regex):
                        q_matched = True

                if q_matched:
                    any_query_matched = True
                    break

            if any_query_matched:
                # Build result info
                is_section = node["node_type"] == "section"

                result = {
                    "node_id": node_id,
                    "label": node.get("label", node_id.split("::")[-1]),
                    "title": node.get("title", "") if is_section else "",
                    "type": "section" if is_section else "content",
                    "file_id": node["file_id"],
                }

                # Provide excerpt and preview
                if not is_section:
                    content = node.get("content", "")
                    # Preview is the beginning of the content with last 5 chars preserved when truncated
                    if len(content) > 100:
                        result["content_preview"] = content[:92] + "..." + content[-5:]
                    else:
                        result["content_preview"] = content

                    # Excerpt is the context around the match
                    excerpt_q = queries[0]
                    if use_regex:
                        result["excerpt"] = result["content_preview"]
                    else:
                        pos = content.lower().find(excerpt_q.lower()) if not case_sensitive else content.find(excerpt_q)
                        if pos != -1:
                            start = max(0, pos - 40)
                            end = min(len(content), pos + len(excerpt_q) + 60)
                            result["excerpt"] = (content[start:end]).strip()
                            if start > 0: result["excerpt"] = "..." + result["excerpt"]
                            if end < len(content): result["excerpt"] = result["excerpt"] + "..."
                        else:
                            result["excerpt"] = result["content_preview"]
                else:
                    # For sections, excerpt could be the title or label
                    result["excerpt"] = result["title"] or result["label"]
                    result["content_preview"] = ""

                results.append(result)
                seen_ids.add(node_id)

        response = {
            "query": query,
            "scope": scope,
            "results": results,
            "total_count": len(results),
            "has_more": len(results) >= max_results,
            "searched_modules": len(self.km.loaded_modules),
            "total_modules": len(self.km.available_modules),
            "options": {
                "whole_word": whole_word,
                "case_sensitive": case_sensitive,
                "use_regex": use_regex
            }
        }

        # Cache the result
        self._search_cache[query_key] = response
        return response

    def clear_cache(self) -> None:
        """Clear the search results cache."""
        self._search_cache.clear()
