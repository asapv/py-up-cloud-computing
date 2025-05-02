import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os

load_dotenv()

class Extractor:
    def __init__(self, video_urls, max_attempts=3, headless=True):
        """
        Initializes the Extractor for SVG heatmap extraction.

        :param video_urls: List of YouTube video URLs.
        :type video_urls: list
        :param max_attempts: Maximum number of attempts to extract SVG.
        :type max_attempts: int
        :param headless: Whether to run browser in headless mode.
        :type headless: bool
        """
        self.video_urls = video_urls
        self.max_attempts = max_attempts
        self.headless = headless
        self.driver = None
        self.configure_webdriver()

    def configure_webdriver(self):
        """
        Configures the Firefox WebDriver with custom profile and options.

        :return: None
        :rtype: None
        """
        self.options = FirefoxOptions()
        profile_path = os.getenv("FIREFOX_PROFILE_PATH")
        if not profile_path:
            raise ValueError("FIREFOX_PROFILE_PATH environment variable not set.")
        self.options.set_preference("profile", profile_path)
        self.options.add_argument("--private")
        self.options.add_argument("--disable-popup-blocking")
        
        if self.headless:
            self.options.add_argument("--headless")

        self.driver = webdriver.Firefox(options=self.options)
        self.driver.get("about:blank")

    def search_and_open_video(self, query, first_time=False):
        """
        Searches for and opens a YouTube video.

        :param query: YouTube video URL or search query.
        :type query: str
        :param first_time: Whether this is the first video being processed.
        :type first_time: bool
        :return: True if successful, False otherwise.
        :rtype: bool
        """
        try:
            if first_time:
                self.driver.get("https://www.youtube.com/")
                search_bar = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.NAME, "search_query"))
                )
            else:
                search_bar = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.NAME, "search_query"))
                )

            time.sleep(1)
            search_bar.clear()
            search_bar.send_keys(query)
            search_bar.send_keys(Keys.RETURN)

            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//ytd-item-section-renderer"))
            )

            first_video_xpath = "(//ytd-video-renderer//a[@id='video-title' and contains(@href, 'watch')])[1]"

            video_link = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, first_video_xpath))
            )

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", video_link)
            time.sleep(1)
            video_link.click()
            return True
        except Exception as e:
            print(f"[search_and_open_video] Error: {str(e)}")
            return False

    def wait_for_video_to_load(self):
        """
        Waits for the video page to load and prepares for SVG extraction.

        :return: True if successful, False otherwise.
        :rtype: bool
        """
        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ytp-play-button"))
            )
            time.sleep(3)

            play_button = self.driver.find_element(By.CLASS_NAME, "ytp-play-button")
            if "Reproducir" in play_button.get_attribute("aria-label") or "Play" in play_button.get_attribute("aria-label"):
                play_button.click()
                time.sleep(1)

            hoverable = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ytp-progress-bar-container"))
            )

            for _ in range(6):
                ActionChains(self.driver).move_to_element(hoverable).perform()
                time.sleep(1.5)

            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'ytp-heat-map')]"))
            )
            return True
        except Exception as e:
            print(f"[wait_for_video_to_load] Error: {str(e)}")
            return False

    def get_svg(self):
        """
        Extracts the SVG heatmap from the video page.

        :return: SVG HTML content, "Not available", or None on error.
        :rtype: str or None
        """
        try:
            time.sleep(3)
            try:
                heatmap_chapter = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ytp-heat-map-chapter"))
                )
                svg_html = heatmap_chapter.get_attribute("innerHTML")
                return svg_html
            except Exception:
                return "Not available"
        except Exception as e:
            print(f"[get_svg] General error: {str(e)}")
            return None

    def get_svg_dict(self):
        """
        Extracts SVG heatmaps for all video URLs.

        :return: Dictionary mapping video URLs to their SVG content or error message.
        :rtype: dict
        """
        svg_results = {}
        first_time = True
        
        urls_to_process = [url for url in self.video_urls]
        
        if len(self.video_urls) != len(urls_to_process):
            print(f"📋 Resuming from checkpoint: {len(self.video_urls) - len(urls_to_process)} videos already processed.")
        
        for i, url in enumerate(urls_to_process):
            print(f"\n🔍 Processing video {i+1}/{len(urls_to_process)}: {url}")
            svg = None

            for attempt in range(1, self.max_attempts + 1):
                print(f"🔄 Attempt {attempt}/{self.max_attempts}")
                try:
                    if not self.search_and_open_video(url, first_time=first_time):
                        print(f"⚠️ Search failed on attempt {attempt}")
                        time.sleep(2)
                        continue

                    first_time = False

                    if not self.wait_for_video_to_load():
                        print(f"⚠️ Failed to load video properly on attempt {attempt}")
                        time.sleep(2)
                        continue

                    svg = self.get_svg()
                    if svg is None:
                        print("⚠️ Error during SVG extraction, retrying...")
                        time.sleep(2)
                        continue
                    elif svg == "Not available":
                        print("ℹ️ SVG not available for this video.")
                        break
                    else:
                        print("✅ SVG successfully extracted.")
                        break

                except Exception as e:
                    print(f"❌ Exception during attempt {attempt}: {e}")
                    time.sleep(2)

            if svg is None:
                svg = "Failed after max attempts"
                print(f"❌ Failed to extract SVG after {self.max_attempts} attempts.")
                
            svg_results[url] = svg
        
        self.driver.quit()
        return svg_results