"""LinkedIn browser-based search and post extraction.

Connects to the user's already-running Chrome via CDP (Chrome DevTools Protocol).
No separate Chrome window is launched.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

CDP_PORT = 9222


class LinkedInBrowser:
    """Searches LinkedIn and extracts posts by connecting to the user's running Chrome.

    Chrome must be started with: chrome.exe --remote-debugging-port=9222
    Use the included start_chrome.bat to do this easily.
    """

    def __init__(self):
        self.driver = None

    def _ensure_driver(self):
        if self.driver:
            return

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ImportError:
            raise RuntimeError("Selenium not installed. Run: pip install selenium webdriver-manager")

        options = Options()
        options.debugger_address = f"127.0.0.1:{CDP_PORT}"

        try:
            self.driver = webdriver.Chrome(options=options)
            logger.info(f"Connected to Chrome on port {CDP_PORT}")
        except Exception as e:
            raise RuntimeError(
                f"Could not connect to Chrome on port {CDP_PORT}.\n\n"
                f"Please do this:\n"
                f"1. Close ALL Chrome windows\n"
                f"2. Run start_chrome.bat (in the app folder)\n"
                f"   OR open CMD and run:\n"
                f'   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222\n'
                f"3. Log into LinkedIn in that Chrome window\n"
                f"4. Try again\n\n"
                f"Error: {e}"
            )

    def is_logged_in(self) -> bool:
        try:
            self._ensure_driver()
            current = self.driver.current_url
            if "linkedin.com" not in current:
                self.driver.get("https://www.linkedin.com/feed/")
                time.sleep(3)
            url = self.driver.current_url
            return "linkedin.com" in url and "login" not in url
        except Exception as e:
            logger.error(f"Login check failed: {e}")
            return False

    def search(self, query: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Search LinkedIn for posts matching the query."""
        self._ensure_driver()
        posts = []

        try:
            search_url = (
                "https://www.linkedin.com/search/results/content/"
                f"?keywords={query.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER"
            )
            self.driver.get(search_url)
            time.sleep(4)

            if "login" in self.driver.current_url:
                logger.warning("Not logged into LinkedIn")
                return posts

            # Scroll to load more results
            for _ in range(max(1, max_results // 10)):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                post_elements = self.driver.find_elements("css selector", "div.feed-shared-update-v2")
                if len(post_elements) >= max_results:
                    break

            post_elements = self.driver.find_elements("css selector", "div.feed-shared-update-v2")
            logger.info(f"Found {len(post_elements)} post elements on LinkedIn")

            for i, elem in enumerate(post_elements[:max_results]):
                try:
                    post = self._extract_post(elem)
                    if post and post.get("text"):
                        posts.append(post)
                except Exception as e:
                    logger.debug(f"Failed to extract post {i}: {e}")

        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")

        logger.info(f"Extracted {len(posts)} posts from LinkedIn search for '{query}'")
        return posts

    def get_post(self, url: str) -> Optional[dict[str, Any]]:
        """Fetch a single LinkedIn post by URL."""
        self._ensure_driver()

        try:
            self.driver.get(url)
            time.sleep(4)

            if "login" in self.driver.current_url:
                return None

            post_elem = self.driver.find_element("css selector", "div.feed-shared-update-v2")
            return self._extract_post(post_elem)
        except Exception as e:
            logger.error(f"Failed to fetch post: {e}")
            return None

    def _extract_post(self, elem) -> dict[str, Any]:
        """Extract structured data from a LinkedIn post element."""
        post = {
            "url": "",
            "title": "",
            "text": "",
            "author_name": "",
            "author_title": "",
            "organization": "",
            "date_posted": None,
            "engagement_likes": 0,
            "engagement_comments": 0,
            "engagement_shares": 0,
            "hashtags": [],
            "mentioned_companies": [],
            "mentioned_orgs": [],
            "mentioned_tech": [],
            "source": "linkedin",
        }

        try:
            links = elem.find_elements("css selector", "a[href*='/posts/']")
            if links:
                post["url"] = links[0].get_attribute("href").split("?")[0]
            else:
                see_more = elem.find_elements("css selector", "a[href*='linkedin.com']")
                if see_more:
                    post["url"] = see_more[0].get_attribute("href").split("?")[0]
        except Exception:
            pass

        try:
            author_elem = elem.find_element("css selector", "span.feed-shared-actor__name")
            post["author_name"] = author_elem.text.strip()
        except Exception:
            pass

        try:
            title_elem = elem.find_element("css selector", "span.feed-shared-actor__headline")
            post["author_title"] = title_elem.text.strip()
            if " at " in post["author_title"]:
                post["organization"] = post["author_title"].split(" at ")[-1].strip()
            elif " @ " in post["author_title"]:
                post["organization"] = post["author_title"].split(" @ ")[-1].strip()
        except Exception:
            pass

        try:
            text_selectors = [
                "div.feed-shared-text__text-view",
                "span.feed-shared-text__text-view",
                "div.feed-shared-update-v2__description",
                "div.update-components-text",
            ]
            for selector in text_selectors:
                text_elems = elem.find_elements("css selector", selector)
                if text_elems:
                    post["text"] = " ".join(te.text.strip() for te in text_elems if te.text.strip())
                    break
            if not post["text"]:
                post["text"] = elem.text.strip()[:2000]
        except Exception:
            pass

        try:
            hashtag_elems = elem.find_elements("css selector", "a[href*='hashtag/']")
            post["hashtags"] = [
                ht.get_attribute("href").split("hashtag/")[-1].split("?")[0]
                for ht in hashtag_elems
                if ht.get_attribute("href") and "hashtag/" in (ht.get_attribute("href") or "")
            ]
        except Exception:
            pass

        try:
            reactions = elem.find_elements("css selector", "span.social-details-react-count")
            for r in reactions:
                count_text = r.text.strip().replace(",", "").replace("+", "")
                if count_text.isdigit():
                    post["engagement_likes"] = max(post["engagement_likes"], int(count_text))
        except Exception:
            pass

        text_lower = post["text"].lower()
        tech_keywords = [
            "ai", "machine learning", "deep learning", "llm", "generative ai",
            "synthetic biology", "precision fermentation", "biotech", "bioprocess",
            "digital twin", "industry 4.0", "automation", "robotics",
            "technology transfer", "ip commercialization", "patent",
            "climate tech", "carbon credit", "circular economy", "sustainability",
            "agtech", "precision agriculture", "biostimulant",
        ]
        for tech in tech_keywords:
            if tech in text_lower:
                post["mentioned_tech"].append(tech)

        return post

    def close(self):
        """Disconnect from Chrome. Does NOT close the browser."""
        self.driver = None

    def __del__(self):
        self.close()
