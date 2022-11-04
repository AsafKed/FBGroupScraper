import time
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

class FBScraper:
    def __init__(self, chrome_driver_path: str, email: str, password: str, hide= False):
        self.CHROME_DRIVER_PATH = chrome_driver_path
        self.EMAIL = email
        # TODO set this to None after initial login
        self.PASSWORD = password

    def setGroupInfo(self, group_ids, group_descriptions= None, search_prompts= None):
        # Set IDs and descriptions
        print("Setting group info")
        self.GROUP_IDS = group_ids
        self.GROUP_URLS = []
        for id in self.GROUP_IDS:
            item = 'https://www.facebook.com/groups/'
            item = item + str(id) if type(id) is not str else item + id
            self.GROUP_URLS.append(item)

        self.GROUP_DESCRIPTIONS = group_descriptions

        self.SEARCH_PROMPTS = search_prompts        
    
    def closeSession(self):
        print("Session closed!")
        self.driver.quit()

    def openAndLogin(self, hide=False):
        print ("Opening Facebook")
        # TODO add if user wishes to do this and self.PASSWORD is None, request entry

        # Webdriver options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--disable-notifications')
        if hide is True:
            chrome_options.add_argument('headless')

        driver = webdriver.Chrome(self.CHROME_DRIVER_PATH, options=chrome_options) #USER INPUT
        driver.get('https://www.facebook.com/')

        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='_42ft _4jy0 _9xo6 _4jy3 _4jy1 selected _51sy']"))).click()
        email = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"input[name = 'email']")))
        password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"input[name = 'pass']")))


        email.clear()
        password.clear()

        email.send_keys(self.EMAIL) #USER INPUT
        password.send_keys(self.PASSWORD) #USER INPUT

        # Open window, select group
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button[type = 'submit']"))).click()

        #maximize window
        driver.maximize_window()
        
        # Set the driver for the class
        self.driver = driver

    def removeCommentFromURL(self, comment):
        return comment.partition('?comment')[0]
    
    def getPostURLs(self, limit: int, group_index: int):
        """ Get a list of post URLs from the Facebook group of choice.

        Args: 
            limit (int): number of post URLs that should be returned.
            group_url (str): the URL of the group to be scraped.

        Returns:
            posts (list): list of post URLs.
        """

        group_url = self.GROUP_URLS[group_index]
        group_id = self.GROUP_IDS[group_index]
        print(f"Opening group with id {group_id}")

        # Open the group page
        self.driver.get(group_url)

        posts = []
        scroll = 0

        print("Collecting comments")
        while len(posts) <= limit:
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
            time.sleep(5)
            
            print(f"scroll {scroll}...")
            scroll += 1

            # In case this may be useful one day, currently this fails, although path is correct.
            # post_xpath = f"//a[contains(@href, 'groups/{group_id}/posts') and not(contains(@href, '?comment_id='))]"
            # new_posts = self.driver.find_elements(By.XPATH, post_xpath)
            # new_posts = [post.get_attribute('href') for post in new_posts]
            # print (new_posts)
            # print (len(new_posts))

            xpath_comments = f"//a[contains(@href, 'groups/{group_id}/posts')]"
            new_comments = self.driver.find_elements(By.XPATH, xpath_comments)
            new_comments = [comment.get_attribute('href') for comment in new_comments]
            
            # Only extract the post URL, not interested in the comment links.
            new_posts = set(self.removeCommentFromURL(comment) for comment in new_comments if self.removeCommentFromURL(comment) not in posts)
            posts.extend(list(new_posts))

            # Remove duplicates
            posts = list(set(posts))

            # Print progress
            if len(posts) < limit:
                print ('Posts total:', len(posts))
            else:
                print ('Posts total:', limit)
        
        self.posts = posts[:limit]

    def getPosterURL(self, post: str, page_source=None, soup=None):
        """ Based on a post URL, get the URL of the poster profile.

        Args:
            post (str): the URL of the group post.
            group_index (int): index of the group to be scraped (from GROUP_IDS and GROUP_URLS).

        Returns:
            url (str): URL of the poster profile.
        
        """
        self.driver.get(post)
        time.sleep(1)
        poster_class = "x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xzsf02u x1s688f"

        # TODO this if stuff is probs very redundant
        link = self.driver.page_source if page_source is None else page_source
        page_source = 'https://www.facebook.com' + page_source if link is None else link

        soup = BeautifulSoup(page_source, 'html.parser') if soup is None else soup

        urls = soup.find_all('a', class_=poster_class)
        urls = [url['href'] for url in urls]

        # Filter for users, then take (what should be the only) result
        url = [url for url in urls if '/user/' in url][0]

        url = "https://www.facebook.com" + str(url)

        return url

def findComments(soup, driver, commentCount):
    # THIS FINDS COMMENT TEXT
    foundCommentCount = 0
    actualComments = soup.find_all('div', class_ = "xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs")
    while (foundCommentCount < commentCount):
        print ('Found count', len(actualComments))
        for i in range(0, len(actualComments)):
            print (actualComments[i].div.string)
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
        time.sleep(5)
        actualComments.extend(soup.find_all('div', class_ = "xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs"))

    for i in range(0, len(actualComments)):
        print (actualComments[i].div.string)

# TODO find user name (and contact info, more if possible) as well
# TODO scrolls for finding all comments?
# Click "Show more" comments button
        # if commentCount > 4:
        #     WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[@class='x78zum5 x1w0mnb xeuugli']"))).click()
# TODO end: check that ALL comments are actually found
# The following finds based on bubbles (which includes person names in the span element)
# commentBubbles = soup.find_all('div', class_="x1ye3gou xwib8y2 xn6708d x1y1aw1k")
# print ('count', len(commentBubbles))
# print (commentBubbles[0].div.extract)
# print (commentBubbles[0].div)
# TODO handle comment text for text AND for emoji usage
