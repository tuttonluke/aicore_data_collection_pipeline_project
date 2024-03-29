#%%
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from waterstones_scraper_headless import WaterstonesScraperHeadless
import os
import pandas as pd
import time
#%%
class QueryWaterstonesHeadless(WaterstonesScraperHeadless):
    """This class inherits from the WaterstonesScraper class, and includes methods relevant
    to specific search queries. All relevant data about books appearing in the search result
    are stored in the self.language_filtered_DataFrame attribute, which is saved as a .csv file
    along with front cover images at the desired file path.

    Parameters
    ----------
    WaterstonesScraper : class
        Parent class containing methods not specific to a particular search query.
    
    Attributes
    ----------
    self.query : None
                Attribute where search query will be stored.
    self.list_of_language_page_links : list
                Attribute where list of links for language-filtered search pages 
                will be stored.
    self.list_of_book_links : list
                Attribute where list of links for individual books from a search query will
                be stored.
    self.language_filtered_DataFrame : pd.DataFrame
                DataFrame where all relevant data about each book in a search query 
                will be stored. 
    """
    def __init__(self,headless=True) -> None:
        super().__init__(headless=headless)
        self.query = None
        self.list_of_language_page_links = []
        self.list_of_book_links = []
        self.language_filtered_DataFrame = pd.DataFrame(columns=["ID", "Timestamp", "Author", "Title", 
            "Language", "Price (£)", "Image_link"])
    
    def search(self, query) -> webdriver.Chrome:
        """Searches given query in waterstones website searchbar.

        Returns
        -------
        webdriver.Chrome
            Chrome webdriver.
        """
        self.query = query.replace(" ", "_").lower()
        search_bar = self.driver.find_element(by=By.XPATH, 
            value="//input[@class='input input-search']")
        search_bar.click()
        try:
            search_bar.send_keys(self.query.replace("_", " "))
            search_bar.send_keys(Keys.RETURN)
        except:
            print("Invalid query input.")

        return self.driver

    def get_language_filter_page_links(self) -> webdriver.Chrome:
        """Populates self.list_of_language_page_links with all the links to 
        language-filtered query results.

        Returns
        -------
        webdriver.Chrome
            Chrome webdriver.
        """
        # Find language section of the filter bar (not always in the same place!)
        search_filters = self.driver.find_elements(by=By.XPATH, 
            value="//div[@class='filter-header slide-trigger js-filter-trigger']") 
        language_tag = None
        for filter in search_filters:
            if filter.text == "LANGUAGE":
                language_tag = filter
        language_container = self.driver.execute_script("""
        return arguments[0].nextElementSibling""", language_tag)
        # find list of relevant links
        language_list = language_container.find_elements(by=By.TAG_NAME, value="a")
        for language in language_list:
            language_link = language.get_attribute("href")
            self.list_of_language_page_links.append(language_link)
        # remove link for "less" button if present (only present with more than 5 languages)
        if len(self.list_of_language_page_links) > 6:
            self.list_of_language_page_links.pop()

        return self.driver

    def get_all_book_links_from_page(self) -> webdriver.Chrome:
        """Populates self.list_of_book_links with all the links to books on the
        current page.

        Returns
        -------
        webdriver.Chrome
            Chrome webdriver.
        """
        self.list_of_book_links = []
        self.display_all_results()
        book_container = self.driver.find_element(by=By.XPATH, 
            value="//div[@class='search-results-list']")
        book_list = book_container.find_elements(by=By.XPATH, value="./div")
        for book in book_list:
            a_tag = book.find_element(by=By.TAG_NAME, value="a")
            link = a_tag.get_attribute("href")
            self.list_of_book_links.append(link)
        print(f"Number of items is {len(self.list_of_book_links)}.")

        return self.driver
    
    def get_language_name(self) -> str:
        """Scrapes language name from language-filtered query results page.

        Returns
        -------
        language_name.test : str
                Name of the language which is filtering search results.
        """
        language_name = self.driver.find_element(by=By.XPATH, 
            value="/html/body/div[1]/div[3]/div[3]/div[1]/div[1]/div/span")
        return language_name.text
    
    def create_DataFrame_of_page_data(self) -> pd.DataFrame:
        """Calls scraping methods to obtain ISBN, author name, book title,
        price, and image link from the current page, returning the information
        in a pandas DataFrame.

        Returns
        -------
        page_df : pd.DataFrame
            DataFrame including all relevant data from the current page. Data
            for language is assigned elsewhere.
        """
        index = 0
        page_df = pd.DataFrame(columns=["ID", "Timestamp", "Author", "Title", 
            "Language", "Price (£)", "Image_link"])
        for book_link in self.list_of_book_links[:1]:
            self.driver.get(book_link)
            isbn = self.get_ISBN()
            author = self.get_author()
            title = self.get_title()
            price = self.get_price()
            image = self.get_image_link()
            book_dict = {
                        "ID" : isbn,
                        "Timestamp" : time.ctime(), # timestamp of scraping.
                        "Author" : author, 
                        "Title" : title,
                        "Language" : None,
                        "Price (£)" : price,
                        "Image_link" : image
                        }
            df = pd.DataFrame(book_dict, index=[index])
            page_df = pd.concat([page_df, df])
            index += 1
    
        return page_df
    
    def get_DataFrame_of_language_filtered_query_results(self):
        """Populates self.language_filtered_DataFrame with data from all
        language-filtered query results.

        Returns
        -------
        self.language_filtered_DataFrame : pd.DataFrame
            Returns attribute self.language_filtered_DataFrame.
        """
        for language_link in self.list_of_language_page_links:
            self.driver.get(language_link)
            try:
                language_name = self.get_language_name()
            except:
                # this runs if the page does not identify language
                language_name = None
            try:
                self.get_all_book_links_from_page()
            except:
                # this runs if there is only one book in the query search
                current_url = self.driver.current_url
                self.list_of_book_links = [current_url]
            page_df = self.create_DataFrame_of_page_data()
            page_df["Language"] = language_name
            self.language_filtered_DataFrame = pd.concat([self.language_filtered_DataFrame,
            page_df], ignore_index=True)
        
        return self.language_filtered_DataFrame.astype(str)
    
    def save_df_as_csv(self):
        """Saves self.language_filtered_DataFrame to a .csv file in
        a folder with the name of the search query, within the raw_data
        folder.
        """
        if not os.path.exists(f"{self.raw_data_path}/{self.query}"):
            os.mkdir(f"{self.raw_data_path}/{self.query}")
        self.language_filtered_DataFrame.to_csv(f"{self.raw_data_path}/{self.query}/{self.query}.csv")
    
    def save_imgs_as_jpg(self):
        """Saves images found in the Image_link column of self.language_filtered_DataFrame 
        in images folder, in the folder with the name of the search query.
        """
        os.mkdir(f"{self.raw_data_path}/{self.query}/images")
        for img_url in self.language_filtered_DataFrame["Image_link"]:
            isbn = img_url[-17:-4]
            self.download_img(img_url, f"{self.raw_data_path}/{self.query}/images/{isbn}.jpg")
#%%
def run_the_scraper():
    """The user inputs desired search queries one at a time which 
    are iteratively appended to the author_list list. The function 
    then instantiates the QueryWaterstonesHeadless class for each 
    query and calls all relevant methods to scrape and save desired 
    data.
    """
    author_list = []
    while True:
        author = input("Enter author, or press ENTER to proceed: ")
        if author != "":
            author_list.append(author)
        else:
            break
    
    print(author_list)
    for author in author_list:
        driver = QueryWaterstonesHeadless(headless=True)
        driver.load_and_accept_cookies()
        driver.search(author)
        driver.get_language_filter_page_links()
        driver.get_DataFrame_of_language_filtered_query_results()
        driver.save_df_as_csv()
        driver.save_imgs_as_jpg()
    driver.quit_browser()    
#%%
if __name__ == "__main__":
    run_the_scraper()