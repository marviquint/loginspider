import scrapy
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from scrapy_selenium import SeleniumRequest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from urllib.parse import urlparse, parse_qs
from selenium.common.exceptions import TimeoutException, WebDriverException



class GrcSpider(scrapy.Spider):
    name = "grc_spider"
    start_urls = ["dashboard"]

    def __init__(self, username="username", password="password", *args, **kwargs):
        super(GrcSpider, self).__init__(*args, **kwargs)
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome(executable_path="path")
        self.driver.maximize_window()

    def start_requests(self):
        # Start by logging in using Selenium
        self.driver.get("login")
        username_input = self.driver.find_element(By.NAME, "username")
        password_input = self.driver.find_element(By.NAME, "password")
        login_button = self.driver.find_element(By.XPATH, "//button")
        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        login_button.click()

        # Wait for the page to load
        WebDriverWait(self.driver, 120).until(
            EC.presence_of_element_located((By.ID, "HEADER_MY_TASKS_text"))
        )

        # Once logged in, crawl the tasks using Scrapy
        yield SeleniumRequest(
            url="dashboard",
            wait_time=120,
            screenshot=True,
            callback=self.parse_dashboard,
            dont_filter=True,
            meta={'driver': self.driver}
        )
    
    def parse_dashboard(self, response: HtmlResponse):
        # Click My Tasks link using JavaScript
        my_tasks_link = response.meta['driver'].find_element(By.ID, "HEADER_MY_TASKS_text").find_element(By.TAG_NAME, 'a')
        response.meta['driver'].execute_script("arguments[0].click();", my_tasks_link)

        # Wait for the page to load
        WebDriverWait(response.meta['driver'], 120).until(
            EC.presence_of_element_located((By.ID, "insert-taskTitle"))
        )

        # Once on My Tasks page, crawl the tasks using Scrapy
        yield SeleniumRequest(
            url=response.url,
            wait_time=120,
            screenshot=True,
            callback=self.parse_tasks,
            dont_filter=True,
            meta={'driver': response.meta['driver']}
        )

    def parse_tasks(self, response: HtmlResponse):
        # Wait for the filter option to be clickable
        filter_option_selector1 = '#taskF'
        WebDriverWait(response.meta['driver'], 120).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, filter_option_selector1))
        )

        # Click the first filter option using JavaScript
        filter_option = response.meta['driver'].find_element(By.CSS_SELECTOR, filter_option_selector1)
        response.meta['driver'].execute_script("arguments[0].click();", filter_option)

        filter_option_selector2 = '#insert-taskTitle li:nth-child(1) .filter4'
        WebDriverWait(response.meta['driver'], 120).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, filter_option_selector2))
        )

        # Click the first filter option using JavaScript
        filter_option2 = response.meta['driver'].find_element(By.CSS_SELECTOR, filter_option_selector2)
        response.meta['driver'].execute_script("arguments[0].click();", filter_option2)

       # Wait for the page to load
        try:
            WebDriverWait(response.meta['driver'], 120).until(
                EC.presence_of_element_located((By.TAG_NAME, 'a'))
            )
        except TimeoutException:
            print('Timeout: Page did not load within 2 minutes')

        # Find all the document links using JavaScript
        try:
            document_links = response.meta['driver'].execute_script("return Array.from(document.getElementsByTagName('a')).filter(a => a.href !== '');")
        except Exception:
            print('Error: Failed to execute JavaScript code')

        for i, document_link in enumerate(document_links, start=1):
            # Check if the link contains the workspace nodeRef
            if 'workspace://SpacesStore/' in document_link.get_attribute('href'):
                # Extract the href attribute value from the document link
                document_link_url = document_link.get_attribute('href')

                # Get the unique document id from the document link url
                unique_id = document_link_url.split('/')[-1]

                # Construct the new url to open the document page
                document_url = f"unique"

                # Click the document link to open the document page in a new tab using JavaScript
                try:
                    response.meta['driver'].execute_script(f"window.open('{document_url}');")
                except Exception:
                    print(f"Error: Failed to execute JavaScript code for document {i}")

                # Switch to the new tab
                response.meta['driver'].switch_to.window(response.meta['driver'].window_handles[-1])

                # Wait for the document title and document properties to load
                try:
                    WebDriverWait(response.meta['driver'], 120).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'node-info')),
                        EC.presence_of_element_located((By.CLASS_NAME, 'field-item'))
                    )
                except TimeoutException:
                    print(f'Timeout: Failed to load document {i} within 2 minutes')

                # Extract the document title and properties using class names
                try:
                    document_title = response.meta['driver'].find_element_by_class_name('node-info').text
                    document_properties = response.meta['driver'].find_elements_by_class_name('field-item')
                except Exception:
                    print(f'Error: Failed to find document {i} elements')

                # Store the document data in a dictionary
                properties_dict = {}
                for prop in document_properties:
                    key = prop.find_element_by_tag_name('label').text.strip()
                    value = prop.find_element_by_class_name('field-item').text.strip()
                    properties_dict[key] = value

                document_data = {
                    'title': document_title.strip(),
                    'properties': properties_dict,
                    'url': response.meta['driver'].current_url
                }

                print(document_data) # Print the scraped data

                # Close the document tab using JavaScript
                close_tab_js = "window.close();"
                try:
                    response.meta['driver'].execute_script(close_tab_js)
                except Exception:
                    print(f"Error: Failed to close document {i} tab")

                # Switch back to the task list tab
                response.meta['driver'].switch_to.window(response.meta['driver'].window_handles[0])

                # Wait for the task list page to load
                try:
                    WebDriverWait(response.meta['driver'], 120).until(
                        EC.presence_of_element_located((By.ID, 'tasksGridContainer'))
                    )
                except TimeoutException:
                    print('Timeout: Task list page did not load within 2 minutes')

                # Check if there are more pages of tasks
                next_button = response.meta['driver'].find_element_by_css_selector('a[id^="yui-pg"]').find_element_by_xpath('./following-sibling::a')
                if next_button.get_attribute('title') == 'Next Page':
                    # Click the next page button to load the next page of tasks
                    next_button.click()

                    # Parse the next page of tasks recursively
                    yield from self.parse(response)


    def handle_error(self, failure):
        # Log any errors
        self.logger.error(repr(failure))
        
    def closed(self, response):
        self.driver.quit()

