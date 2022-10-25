import time

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
