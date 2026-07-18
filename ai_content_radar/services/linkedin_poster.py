"""LinkedIn posting service - posts comments to the user's running Chrome.

Connects via CDP (Chrome DevTools Protocol) so no separate Chrome window is opened.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

CDP_PORT = 9222


class LinkedInPoster:
    """Posts comments to LinkedIn by connecting to the user's running Chrome.

    Chrome must be started with: chrome.exe --remote-debugging-port=9222
    """

    def __init__(self):
        self.driver = None

    def _ensure_driver(self):
        """Connect to the user's running Chrome via CDP."""
        if self.driver:
            return

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ImportError:
            raise RuntimeError(
                "Selenium not installed. Run: pip install selenium webdriver-manager"
            )

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
        """Check if user is logged into LinkedIn."""
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

    def post_comment(self, post_url: str, comment_text: str) -> dict:
        """Post a comment on a LinkedIn post using the user's browser."""
        result = {"success": False, "message": "", "url": post_url}

        try:
            self._ensure_driver()

            self.driver.get(post_url)
            time.sleep(3)

            if "login" in self.driver.current_url:
                result["message"] = "Not logged into LinkedIn."
                return result

            self.driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(2)

            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            comment_box = None
            selectors = [
                "div[contenteditable='true'][data-placeholder*='comment']",
                "div[contenteditable='true'][aria-label*='comment']",
                "div[contenteditable='true'][aria-label*='Add a comment']",
                "div.ql-editor[contenteditable='true']",
                "div.comments-comment-box div[contenteditable='true']",
                "div[role='textbox'][contenteditable='true']",
            ]

            for selector in selectors:
                try:
                    comment_box = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except Exception:
                    continue

            if not comment_box:
                try:
                    comment_buttons = self.driver.find_elements(
                        By.XPATH,
                        "//button[contains(@aria-label, 'Comment') or contains(@aria-label, 'comment')]"
                    )
                    for btn in comment_buttons:
                        if btn.is_displayed():
                            btn.click()
                            time.sleep(2)
                            break

                    for selector in selectors:
                        try:
                            comment_box = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            break
                        except Exception:
                            continue
                except Exception:
                    pass

            if not comment_box:
                result["message"] = "Could not find comment box. The post may not allow comments."
                return result

            comment_box.click()
            time.sleep(1)

            from selenium.webdriver.common.keys import Keys
            for line in comment_text.split("\n"):
                comment_box.send_keys(line)
                comment_box.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(0.1)

            time.sleep(1)

            post_button = None
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    try:
                        span_text = btn.find_element(By.TAG_NAME, "span").text.strip()
                        if span_text == "Post" and btn.is_displayed() and btn.is_enabled():
                            post_button = btn
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            if not post_button:
                try:
                    post_button = self.driver.find_element(
                        By.CSS_SELECTOR, "button[aria-label='Post comment']"
                    )
                except Exception:
                    pass

            if post_button:
                post_button.click()
                time.sleep(3)
                result["success"] = True
                result["message"] = "Comment posted successfully!"
                logger.info(f"Comment posted to {post_url}")
            else:
                result["message"] = "Could not find Post button. Comment was typed but not submitted."

        except Exception as e:
            result["message"] = f"Error posting comment: {str(e)}"
            logger.error(f"LinkedIn posting failed: {e}")

        return result

    def close(self):
        """Disconnect from Chrome. Does NOT close the browser."""
        self.driver = None

    def __del__(self):
        self.close()
