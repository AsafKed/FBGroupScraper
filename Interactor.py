from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class Interactor:
    def __init__(self, driver: webdriver.Chrome, profile_list= None):
        """Initialize the Interactor.

        Args:
            driver (webdriver.Chrome): for opening Facebook.
            profile_list (list): list of profiles to message.
        """
        self.driver = driver
        self.profile_list = profile_list

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
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_msg_btn))).click()

        # Write something in the input
        xpath_input = "//p[@class='xdj266r xat24cr']"
        input_field = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_input)))
        input_field.send_keys(msg)

    def messageAll(self, msg: str, profile_list= None):
        if (profile_list == None) and (self.profile_list == None):
            # TODO turn into error type (must make new file for it)
            print("No profiles entered.")
        elif profile_list != None:
            self.profile_list = profile_list

        for count, profile in enumerate(self.profile_list):
            # print(f"Messaging {count+1}/{len(self.profile_list)}", end='\r')
            print(f"{profile}")
            self.message(profile, msg)