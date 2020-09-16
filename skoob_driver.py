import time
import os
from abc import ABC
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException
)

class WebPage(ABC):
    """Abstract WebPage class. Deals with Selenium API.

    Keyword arguments:
    webdriver -- Needs input driver that is being used.
    """

    def __init__(self, driver=None):
        if not driver:
            self.path = chromedriver_autoinstaller.install()
            self.chromeOptions = webdriver.ChromeOptions()
            self.driver = webdriver.Chrome(self.path, options=self.chromeOptions)
            
        else:
            self.driver = driver

    def start(self, url=''):
        """Starts a Chrome driver for this WebPage, fetches url provided,
        switches to window and maximizes it.
        """
        self.driver.get(url)
        self.main_window = self.driver.current_window_handle
        time.sleep(1)
        self.driver.switch_to.window(self.main_window)
        self.driver.maximize_window()        

    def find_element(self, locator:tuple):
        return self.driver.find_element(*locator)

    def find_elements(self, locator:tuple):
        return self.driver.find_elements(*locator)

    def write_text(self, locator:tuple, text:str):
        return self.driver.find_element(*locator).send_keys(text)

    def get_text(self, locator:tuple):
        try:
            return self.driver.find_element(*locator).text
        except:
            return None

    def hit_enter(self, locator:tuple):
        return self.driver.find_element(*locator).send_keys(Keys.ENTER)

    def _wait_until(self, pattern:str, maxwait=10):
        """Waits until maxwait or until a xpath expression can be found
        in the HTML.
        
        Keyword arguments:
        pattern -- Xpath expression to be looked for.
        maxwait -- Maximum wait time in seconds.
        """
        driver = self.driver
        step = 0
        loaded = False
        while not loaded and step<maxwait:
            time.sleep(1)
            step += 1
            try:
                element = driver.find_element_by_xpath(pattern)
                loaded = True
                break
            except NoSuchElementException:
                loaded = False
            except Exception as e:
                print('Encerrando execucao')
                raise

        return loaded

class HomePage(WebPage):
    """Skoob homepage methods.

    Methods:
    search -- inputs text in search bar and hits ENTER key.
    """

    search_bar = (By.XPATH, '//input[@id="search"]')

    def search(self, text:str):
        self.write_text(self.search_bar, text)
        self.hit_enter(self.search_bar)


class SearchList(WebPage):
    """Skoob search list page methods.

    Methods:
    go_to_result -- Follows link from search result number #.
    """

    results = (By.XPATH, '//div[@class="detalhes"]//a[1]')

    def __init__(self, driver):
        super(SearchList, self).__init__(driver)
        self.result_elements = self.find_elements(self.results)

    def search_results(self)->list:
        try:
            return [result.text for result in self.result_elements]
        except StaleElementReferenceException:
            print("Results not available anymore. Did you leave results page?")

    def go_to_result(self, number:int=0):
        # number 0 = first result

        item = self.result_elements[number]
        item.click()


class Book(object):

    def __init__(self, title, author, synopsis, insb, prices, status):
        self.title = title
        self.author = author
        self.synopsis = synopsis
        self.insb = insb
        self.prices = prices
        self.status = status

        
class BookPage(WebPage):
    """Skoob book page methods.

    Methods:
    fetch_book 
    go_to_recommended -- Follows a link to a random similar book.
    """

    popup_up_locator =(By.XPATH, '//div[@class="modal fade ng-isolate-scope in"]')
    synopsis_locator = (By.XPATH, '//p[@itemprop="description"]')
    synopsis_extend_locator = (By.ID, 'sinopse-extend-bt')
    author_locator = (By.XPATH, '//*[@id="pg-livro-menu-principal-container"]/a')
    recommended_locator = (By.XPATH, '//div[@class="pg-livro-box-similares-capa ng-scope"]')
    insb_13_locator = (By.XPATH, '//div[@class = "sidebar-desc"]/span')
    status_bar_locator = (By.XPATH, "//div[@id = 'livro-perfil-status']/div[@class='bar']")
    prices_locator = (By.XPATH, "//div[@class = 'pg-livro-bt-compra']//a")
    title_locator = (By.ID, 'pg-livro-titulo')

    def __init__(self, driver):

        super(BookPage, self).__init__(driver)

        try: #Deals with popup
            # self._wait_until(find_element(self.popup_up_locator), maxwait=3)
            time.sleep(4)
            self.find_element(self.popup_up_locator).click()

        except:
            pass

    def go_to_recommended(self) -> bool:
        try:
            recommended_list = self.find_elements(self.recommended_locator)
            random.choice(recommended_list).click()
            return True

        except:
            return False

    def fetch_book(self) -> Book:
        try:
            find_element(synopsis_extend_locator).click()
        except:
            pass

        book = Book(
            title=self.get_text(self.title_locator),
            author=self.get_text(self.author_locator),
            synopsis=self.get_text(self.synopsis_locator),
            insb=self.get_text(self.insb_13_locator),
            prices=self.get_prices(),
            status=self.get_status()
        )

        return book

    def get_prices(self) -> dict:
        prices = self.find_elements(self.prices_locator)
        try:
            if len(prices)==2:
                return {
                    'min_price': float(prices[0].text.strip('R$ ').replace(",",".")),
                    'max_price': float(prices[1].text.strip('R$ ').replace(",","."))
                }
            else:
                return {'price': float(prices[0].text.strip('R$ ').replace(",","."))}
        except:
            return {'price': None}


    def get_status(self) -> dict:
        status_bar = self.find_elements(self.status_bar_locator)
        status = {}
        for element in status_bar:
            name = element.find_element_by_xpath(".//a").text
            value = float(element.find_element_by_xpath(".//b").text)
            status[name] = value
        return status


crawler = HomePage()
crawler.start('https://www.skoob.com.br/')
crawler.search('Duna')

searchpage = SearchList(crawler.driver)
time.sleep(2)
searchpage.go_to_result()
book_page = BookPage(searchpage.driver)
print(book_page.fetch_book().title)