import time
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import numpy as np
import pandas as pd

class FBScraper:
    def __init__(self, chrome_driver_path: str, email: str, password: str, hide= False):
        self.CHROME_DRIVER_PATH = chrome_driver_path
        self.EMAIL = email
        # TODO set this to None after initial login
        self.PASSWORD = password

        # Initialize other variables as None
        self.GROUP_IDS = None
        self.GROUP_URLS = None
        self.GROUP_DESCRIPTIONS = None
        self.SEARCH_PROMPTS = None

        self.driver = None

        self.posts = []
        self.all_info = None

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
        print(f"\nOpening group with id {group_id}")

        # Open the group page
        self.driver.get(group_url)

        posts = []
        scroll = 0

        print("Collecting comments")
        while len(posts) <= limit:
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
            time.sleep(5)
            
            # print(f"scroll {scroll}")
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
                print (f"scroll {scroll}, posts {len(posts)}", end='\r')
            else:
                print (f"scroll {scroll}, posts {limit}", end='\r')
            scroll += 1
        
        # Add new posts
        self.posts.extend(posts[:limit])

        # Remove duplicates
        self.posts = list(set(self.posts))

    def getPosterURL(self, post: str):
        """ Based on a post URL, get the URL of the poster profile.

        Args:
            post (str): the URL of the group post.

        Returns:
            url (str): URL of the poster profile.
            name (str): name of the poster.
        
        """
        self.driver.get(post)
        time.sleep(10)
        poster_class = "x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xzsf02u x1s688f"

        # Get soup
        page_source = 'https://www.facebook.com' + self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser') 

        soupy_urls = soup.find_all('a', class_=poster_class)
        urls = [url['href'] for url in soupy_urls]

        # Filter for users, then take (what should be the only) result
        index = [idx for idx, url in enumerate(urls) if '/user/' in url]
        

        # Take the first user (in case of the poster tagging housemates)
        if len(index) > 0:
            index = index[0]
            url = "https://www.facebook.com" + str(urls[index])
            name = soupy_urls[index].contents[0].span
            try:
                name = name.get_text() # removes HTML tags
            except:
                name = np.nan
        else:
            # This may happen if a post is shared, for example
            url = np.nan
            name = np.nan

        return url, name

    # TODO clean up this messy thing
    def getAllInfo(self, amount: int, posts= None):
        # Initialize if not done already
        if self.posts is None:
            self.posts = [] 

        if posts == None:
            # Get specified number of posts from all group
            for i in range(0, len(self.GROUP_IDS)):
                # Updates self.posts
                self.getPostURLs(amount, i)
            # TODO REMOVE! Save this in case of crashing
            temp = pd.DataFrame.from_dict({"Posts": self.posts})
            temp.to_csv('data/test_save.csv', index=False)
        else:
            posts = list(posts['Posts'])
            self.posts = posts

        posters = []
        names = []
        texts = []
        translated_bools = []
        comment_counts = []

        print("\nCollecting from individual posts")
        for post_count, a in enumerate(self.posts):
            print(f"Post {post_count+1}/{len(self.posts)}", end='\r')
            # Open webpage
            self.driver.get(a)
            time.sleep(1)

            poster, name = self.getPosterURL(a)

            # TODO convert all this stuff into methods
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Relevant classes for text (or translate button)
            translate_btn_text = "x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1n2onr6 x87ps6o x1a2a7pz xt0b8zv"
            translate_btn = soup.find('div', class_ = translate_btn_text)
            translated_text_class = "x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h"
            original_text_class = "x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x41vudc x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h"

            if (translate_btn is not None) and (soup.find('div', class_ = translate_btn_text).text == "See Translation"):
                    is_translated = False
                    # Original
                    # text = soup.find('span' , class_ = original_text_class).text #post
                    t = soup.find('div', class_ = "x1swvt13 x1l90r2v x1pi30zi x1iorvi4")
                    if t is not None:
                            text = t.text #post
                    else:
                            # This may result in text="Facebook", could find all of this class and choose one where it doesn't equal Facebook
                            text = soup.find('span' , class_ = original_text_class).text #post

            elif soup.find('span', class_ = translated_text_class) is not None:
                    # Translated
                    text = soup.find('span' , class_ = translated_text_class).text #post
                    is_translated = True

            elif soup.find('span', class_ = original_text_class) is not None:
                    # Original English
                    text = soup.find('span', class_ = original_text_class).text #post
                    is_translated = False

            # is_translated = len(soup.find_all('span', class_ = "x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1pg5gke xvq8zen xo1l8bm x1qq9wsj x1yc453h")) > 0
            # TODO instead of length check that it equals expected text ('See original' or 'Rate this translation')

            comment_count = soup.find('span', class_ = "x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x41vudc x6prxxf xvq8zen xo1l8bm xi81zsa").text
            comment_count = int(re.search(r'\d+', comment_count).group())
            
            # TODO create DF/dictionary/smth with all this info
            posters.append(poster)
            names.append(name)
            texts.append(text)
            translated_bools.append(is_translated)
            comment_counts.append(comment_count)

        print("Creating final all_info DF")
        self.all_info = pd.DataFrame.from_dict({"Text": texts, "Is_Translated": translated_bools, "Comment_Count": comment_counts, 'Post': list(self.posts), 'Poster': list(posters), 'Name': list(names)})
        return self.all_info

    # TODO implement this
    def message(self, profile: str, msg: str):
        # Add enter to message so that it gets sent
        msg_end = msg[len(msg)-2] + msg[len(msg)-1]
        if msg_end != "\n":
            msg = msg + "\n"

        # Open the profile
        self.driver.get(profile)
        
        # Click the "Message" button
        xpath_msg_btn = "//span[contains(text(),'Message')]"
        page_source = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_msg_btn))).click()

        # Write something in the input
        xpath_input = "//p[@class='xdj266r xat24cr']"
        input_field = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_input)))
        input_field.send_keys(msg)

def findComments(soup, driver, comment_count):
    # THIS FINDS COMMENT TEXT
    foundcomment_count = 0
    actualComments = soup.find_all('div', class_ = "xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs")
    while (foundcomment_count < comment_count):
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
        # if comment_count > 4:
        #     WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[@class='x78zum5 x1w0mnb xeuugli']"))).click()
# TODO end: check that ALL comments are actually found
# The following finds based on bubbles (which includes person names in the span element)
# commentBubbles = soup.find_all('div', class_="x1ye3gou xwib8y2 xn6708d x1y1aw1k")
# print ('count', len(commentBubbles))
# print (commentBubbles[0].div.extract)
# print (commentBubbles[0].div)
# TODO handle comment text for text AND for emoji usage: maybe use .content instead of .text
