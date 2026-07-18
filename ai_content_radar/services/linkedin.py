"""Unified LinkedIn service - manages a dedicated Chrome instance for automation.

Uses a separate Chrome profile (--user-data-dir) so it never needs to kill
the user's existing Chrome. Two Chrome instances coexist peacefully.
"""
from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

CDP_PORT = 9222
APP_DATA = Path(os.environ.get("APPDATA", "~")) / "ai_content_radar"
CHROME_PROFILE = APP_DATA / "chrome_profile"

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
]


def _find_chrome() -> Optional[str]:
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    return None


def _is_cdp_running() -> bool:
    import httpx
    try:
        r = httpx.get(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def get_status() -> dict:
    if _is_cdp_running():
        return {"status": "connected", "message": "Chrome is connected and ready."}
    chrome = _find_chrome()
    if not chrome:
        return {"status": "not_found", "message": "Google Chrome is not installed."}
    return {"status": "disconnected", "message": "Chrome is not connected. Click 'Launch' to start."}


def launch_chrome() -> str:
    if _is_cdp_running():
        return "already_running"

    chrome = _find_chrome()
    if not chrome:
        return "not_found"

    CHROME_PROFILE.mkdir(parents=True, exist_ok=True)

    cmd = [
        chrome,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={CHROME_PROFILE}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-sync",
        "https://www.linkedin.com/login",
    ]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for i in range(30):
        time.sleep(0.5)
        if _is_cdp_running():
            return "launched"

    return "launch_timeout"


def get_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.debugger_address = f"127.0.0.1:{CDP_PORT}"
    return webdriver.Chrome(options=options)


def is_logged_in(driver) -> bool:
    try:
        url = driver.current_url
        if "linkedin.com" not in url:
            driver.get("https://www.linkedin.com/feed/")
            time.sleep(4)
            url = driver.current_url
        return "linkedin.com" in url and "login" not in url
    except Exception:
        return False


def search_linkedin(driver, query: str, max_results: int = 20) -> list[dict[str, Any]]:
    """Search LinkedIn for posts using current LinkedIn HTML structure."""
    from selenium.webdriver.common.by import By

    posts = []

    try:
        search_url = (
            "https://www.linkedin.com/search/results/content/"
            f"?keywords={query.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER"
        )
        driver.get(search_url)
        time.sleep(5)

        if "login" in driver.current_url:
            return posts

        # Scroll to load more results
        for _ in range(max(1, max_results // 6)):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # Find all post control menu buttons — these identify individual posts
        control_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            "button[aria-label*='Open control menu for post by']"
        )

        logger.info(f"Found {len(control_buttons)} post control buttons")

        for btn in control_buttons[:max_results]:
            try:
                post = _extract_post_v2(driver, btn)
                if post and post.get("text"):
                    posts.append(post)
            except Exception as e:
                logger.debug(f"Failed to extract post: {e}")
                continue

    except Exception as e:
        logger.error(f"LinkedIn search failed: {e}")

    return posts


def _extract_post_v2(driver, control_btn) -> dict[str, Any]:
    """Extract a post from the new LinkedIn HTML structure."""
    from selenium.webdriver.common.by import By

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

    # Get author from button aria-label
    label = control_btn.get_attribute("aria-label") or ""
    if "Open control menu for post by " in label:
        post["author_name"] = label.replace("Open control menu for post by ", "").strip()

    # Walk up from the button to find a container that has a text box
    container = control_btn
    text_box = None
    for _ in range(10):
        container = container.find_element(By.XPATH, "./..")
        boxes = container.find_elements(By.CSS_SELECTOR, "[data-testid='expandable-text-box']")
        if boxes:
            text_box = boxes[0]
            break

    if not text_box:
        return post

    # Extract text
    post["text"] = text_box.text.strip()
    if not post["text"]:
        return post

    # Find the post URL — look for /pulse/ links (articles) or /posts/ links
    try:
        links = container.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href") or ""
            if "/pulse/" in href:
                post["url"] = href.split("?")[0]
                break
            elif "/posts/" in href and not post["url"]:
                post["url"] = href.split("?")[0]
    except Exception:
        pass

    # Find author profile URL for unique identification
    if not post["url"]:
        try:
            profile_links = container.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
            if profile_links:
                post["url"] = profile_links[0].get_attribute("href").split("?")[0]
        except Exception:
            pass

    # If still no URL, construct one from author name
    if not post["url"]:
        slug = post["author_name"].lower().replace(" ", "-").replace(".", "")
        post["url"] = f"linkedin.com/posts/{slug}"

    # Extract author title from nearby spans
    try:
        spans = container.find_elements(By.CSS_SELECTOR, "span[aria-hidden='true']")
        for span in spans:
            txt = span.text.strip()
            if txt and post["author_name"] in txt:
                # The title is usually in a sibling or nearby span
                parent = span.find_element(By.XPATH, "./..")
                sib_spans = parent.find_elements(By.CSS_SELECTOR, "span[aria-hidden='true']")
                for sib in sib_spans:
                    sib_text = sib.text.strip()
                    if sib_text and sib_text != txt and len(sib_text) > 3:
                        if " at " in sib_text or " @ " in sib_text:
                            post["author_title"] = sib_text
                            if " at " in sib_text:
                                post["organization"] = sib_text.split(" at ")[-1].strip()
                            elif " @ " in sib_text:
                                post["organization"] = sib_text.split(" @ ")[-1].strip()
                        break
    except Exception:
        pass

    # Extract hashtags
    try:
        ht_links = container.find_elements(By.CSS_SELECTOR, "a[href*='HASH_TAG']")
        for ht in ht_links:
            href = ht.get_attribute("href") or ""
            if "keywords=" in href:
                tag = href.split("keywords=")[-1].split("&")[0]
                tag = tag.replace("%23", "").replace("#", "")
                if tag:
                    post["hashtags"].append(tag)
    except Exception:
        pass

    # Detect mentioned technologies
    text_lower = post["text"].lower()
    for tech in [
        "ai", "machine learning", "llm", "generative ai", "synthetic biology",
        "biotech", "digital twin", "industry 4.0", "technology transfer",
        "climate tech", "circular economy", "agtech",
    ]:
        if tech in text_lower:
            post["mentioned_tech"].append(tech)

    return post


def post_comment(driver, post_url: str, comment_text: str) -> dict:
    """Post a comment on a LinkedIn post."""
    result = {"success": False, "message": ""}

    try:
        driver.get(post_url)
        time.sleep(3)

        if "login" in driver.current_url:
            result["message"] = "Not logged into LinkedIn."
            return result

        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(2)

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        comment_box = None
        for selector in [
            "div[contenteditable='true'][data-placeholder*='comment']",
            "div[contenteditable='true'][aria-label*='comment']",
            "div[contenteditable='true'][aria-label*='Add a comment']",
            "div.ql-editor[contenteditable='true']",
            "div[role='textbox'][contenteditable='true']",
        ]:
            try:
                comment_box = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except Exception:
                continue

        if not comment_box:
            try:
                btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Comment')]")
                for btn in btns:
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(2)
                        break
                for selector in [
                    "div[contenteditable='true'][aria-label*='comment']",
                    "div[role='textbox'][contenteditable='true']",
                ]:
                    try:
                        comment_box = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except Exception:
                        continue
            except Exception:
                pass

        if not comment_box:
            result["message"] = "Could not find comment box."
            return result

        comment_box.click()
        time.sleep(0.5)

        from selenium.webdriver.common.keys import Keys
        for line in comment_text.split("\n"):
            comment_box.send_keys(line)
            comment_box.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.1)

        time.sleep(1)

        post_button = None
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                try:
                    span = btn.find_element(By.TAG_NAME, "span").text.strip()
                    if span == "Post" and btn.is_displayed() and btn.is_enabled():
                        post_button = btn
                        break
                except Exception:
                    continue
        except Exception:
            pass

        if not post_button:
            try:
                post_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Post comment']")
            except Exception:
                pass

        if post_button:
            post_button.click()
            time.sleep(3)
            result["success"] = True
            result["message"] = "Comment posted!"
        else:
            result["message"] = "Could not find Post button."

    except Exception as e:
        result["message"] = f"Error: {e}"

    return result


def create_post(driver, text: str, photo_paths: list[str] | None = None) -> dict:
    """Create a new post on the LinkedIn feed."""
    result = {"success": False, "message": ""}

    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(4)

        if "login" in driver.current_url:
            result["message"] = "Not logged into LinkedIn."
            return result

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        start_post = None
        for selector in [
            "button.share-box-feed-entry__trigger",
            "button[aria-label='Start a post']",
            "div[data-control-name='share_box']",
        ]:
            try:
                start_post = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except Exception:
                continue

        if not start_post:
            try:
                spans = driver.find_elements(By.XPATH, "//span[contains(text(), 'Start a post')]")
                for span in spans:
                    parent = span.find_element(By.XPATH, "./..")
                    if parent.is_displayed():
                        parent.click()
                        start_post = True
                        break
            except Exception:
                pass

        if not start_post or start_post is True:
            if start_post is not True:
                result["message"] = "Could not find 'Start a post' button."
                return result

        time.sleep(3)

        editor = None
        for selector in [
            "div[contenteditable='true'][data-placeholder='What do you want to talk about?']",
            "div.ql-editor[contenteditable='true']",
            "div[contenteditable='true'][role='textbox']",
            "div.share-creation-state__editor",
            "div[contenteditable='true']",
        ]:
            try:
                editor = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except Exception:
                continue

        if not editor:
            result["message"] = "Could not find post editor."
            return result

        editor.click()
        time.sleep(0.5)

        from selenium.webdriver.common.keys import Keys
        for line in text.split("\n"):
            editor.send_keys(line)
            editor.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.05)

        time.sleep(1)

        if photo_paths:
            try:
                file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='image']")
                for photo in photo_paths:
                    file_input.send_keys(photo)
                    time.sleep(2)
            except Exception:
                pass

        time.sleep(2)

        post_button = None
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, "button.share-actions__primary-action")
            for btn in buttons:
                if btn.is_displayed() and "Post" in btn.text:
                    post_button = btn
                    break
        except Exception:
            pass

        if not post_button:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    try:
                        if btn.text.strip() == "Post" and btn.is_displayed() and btn.is_enabled():
                            post_button = btn
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        if post_button:
            post_button.click()
            time.sleep(5)
            result["success"] = True
            result["message"] = "Post published!"
        else:
            result["message"] = "Could not find Post button."

    except Exception as e:
        result["message"] = f"Error: {e}"

    return result
