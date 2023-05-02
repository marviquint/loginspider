import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By

class LoginSpider(scrapy.Spider):
    name = "login"
    #start_urls = ["page name"]
    start_urls = ["page name"]

    def start_requests(self):
        # Create a new Selenium WebDriver instance
        #driver = webdriver.Chrome(executable_path = "path")
        driver = webdriver.Chrome(executable_path = "path")
        
        # Navigate to the login page
        #driver.get("page name")
        driver.get("page name")
        
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
