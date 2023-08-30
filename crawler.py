from bs4 import BeautifulSoup
import requests, os, threading
from typing import List, Dict
import json
from urllib.parse import urljoin
from sanitizer import sanitize_dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse

visited_urls = set()
url_lock = threading.Lock()  # Lock for thread-safe operations

# Fetch the webpage content
def fetch_page(url: str) -> str:
    try:
        response = requests.get(url)
        return response.text if response.status_code == 200 else ""
    except Exception as e:
        print(f"Fetch error: {e}")
        return ""

# Parse links from the HTML content
def parse_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    return [urljoin(base_url, a["href"]) for a in soup.find_all("a", href=True)]

# Extract desired content from HTML
def extract_content(html: str) -> Dict:
    soup = BeautifulSoup(html, 'html.parser')
    texts = list(soup.stripped_strings)
    title = soup.title.string if soup.title else ""
    return {"title": title, "content": " ".join(texts)}

# Save the scraped data in JSON format
def save_data(data: Dict, base_domain: str):
    sanitized_data = sanitize_dict(data)
    output_dir = "crawler_data"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    domain_name = base_domain.split("www.")[-1].split("/")[0]
    output_file = os.path.join(output_dir, f"{domain_name}.json")
    
    with open(output_file, "a") as f:
        f.write(json.dumps(sanitized_data) + "\\n")

# Determine whether to follow a link or not
def should_follow_link(url: str, base_url: str) -> bool:
    parsed_url = urlparse(url)
    parsed_base_url = urlparse(base_url)
    
    # If the scheme (http or https) and netloc (www.example.com) match, follow the link
    if parsed_url.scheme == parsed_base_url.scheme and parsed_url.netloc == parsed_base_url.netloc:
        return True
    
    # If only the netloc matches (ignoring www and scheme), follow the link
    if parsed_url.netloc.replace("www.", "") == parsed_base_url.netloc.replace("www.", ""):
        return True
    
    return False

# Fetch and parse the next URLs to crawl
def get_next_urls(base_url: str, html: str) -> List[str]:
    with url_lock:  # Thread-safe operations
        links = parse_links(html, base_url)
        
        # Start a Selenium WebDriver session to find JavaScript links
        driver = webdriver.Chrome()
        driver.get(base_url)
        
        # Find elements that are usually clickable
        clickable_elements = driver.find_elements(By.CSS_SELECTOR, 'button, [onclick], [role="button"]')
        
        clickable_links = [elem.get_attribute('onclick') for elem in clickable_elements if elem.get_attribute('onclick')]
        
        # Close the Selenium session
        driver.close()

        # Combine both regular and clickable links
        all_links = links + clickable_links
        print(all_links)

        # Filter out already visited URLs and add new ones to the set
        next_urls = [link for link in all_links if should_follow_link(link, base_url) and link not in visited_urls]
        visited_urls.update(next_urls)

    return next_urls

# Main crawling function
def main_crawl_function(base_domain: str):
    global visited_urls
    with url_lock:  # Thread-safe operations
        visited_urls.add(base_domain)
    
    html = fetch_page(base_domain)
    if html:
        content = extract_content(html)
        save_data(content, base_domain)
        
        next_urls = get_next_urls(base_domain, html)
        if next_urls:
            threads = []
            for url in next_urls[:5]:  # Limiting to first 5 links for simplicity
                thread = threading.Thread(target=main_crawl_function, args=(url,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to finish
            for thread in threads:
                thread.join()



def start(url):
    base_domain = url.split("//")[-1].split("www.")[-1].split("/")[0]
    base_domain = f"https://www.{base_domain}"
    main_crawl_function(base_domain)