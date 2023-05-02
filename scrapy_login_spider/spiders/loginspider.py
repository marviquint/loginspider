import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By

class LoginSpider(scrapy.Spider):
    name = "login"
    #start_urls = ["page name"]
    start_urls = ["pagename"]
    urls = ["pagename"]

    def start_requests(self):
        # Create a new Selenium WebDriver instance
        #driver = webdriver.Chrome(executable_path = "path")
        driver = webdriver.Chrome(executable_path = "path")
        
        # Navigate to the login page
        #driver.get("page name")
        driver.get("pagename")
        
        # Fill in the form fields
        # username_field = driver.find_element("name", "username")
        # username_field.send_keys("username")
        # password_field = driver.find_element("name", "password")
        # password_field.send_keys("password")


        username_field = driver.find_element("name", "username")
        username_field.send_keys("username")
        password_field = driver.find_element("name", "password")
        password_field.send_keys("password")
        
        # Submit the form
        submit_button = driver.find_element(By.XPATH, "//button")
        submit_button.click()
        
        # Wait for the page to load
        driver.implicitly_wait(10)
        
        # Extract any cookies or tokens needed for subsequent requests
        cookies = driver.get_cookies()
        
        # Send an authenticated request using Scrapy
        for url in self.start_urls:
            yield scrapy.Request(url, cookies=cookies, callback=self.parse)
            
    def parse(self, response):
        # Extract data from the authenticated page
        print("Login Successful!")

        # Follow links to other pages
    #     links = response.css('.yui-dt-col-title .theme-color-1').getall()
    #     for link in links:
    #         child_links = response.css('#yui-rec27 a').getall()

    #         for link in child_links:
    #             yield response.follow(link, callback=self.parse_link)

    # def parse_link(self, response):
    #     # Extract data from the link page
    #     # ...
    #     # Extract title first
    #     document_name = '\u000A'.join(response.css('.node-info .dark').css('::text').getall())
    #     # Extract the rules content
    #     data = '\u000A'.join(response.css('.form-fields').css('::text').getall())
    #     print("Data extracted from page: ", document_name, data)
        
    #     # Store the data in an item
    #     item = {}
    #     item[''+document_name] = data      
