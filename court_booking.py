from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
import time
import pandas as pd


class CourtReservationBot:
    def __init__(self, driver_path: str, url: str, keys: pd.DataFrame, data: dict):
        self.driver_path = driver_path
        self.url = url
        self.keys = keys
        self.data = data

        service = Service(executable_path=self.driver_path)
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=service, options=options)

        self.setup_driver_window()

    def setup_driver_window(self):
        screen_width = self.driver.execute_script("return window.screen.width;")
        screen_height = self.driver.execute_script("return window.screen.height;")
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.8)
        self.driver.set_window_size(window_width, window_height)

    def login(self):
        self.driver.get(self.url)
        try:
            time.sleep(1.5)
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "login_header"))
            )
            login_button.click()

            email = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "loginform-email"))
            )
            email.send_keys(self.keys["email"])

            password = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "loginform-password"))
            )
            password.send_keys(self.keys["password"])

            enter_account = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "login"))
            )
            enter_account.click()
        except (TimeoutException, NoSuchElementException) as e:
            print(f"An error occurred during login: {e}")

    def navigate_to_favorite_club(self):
        try:
            nav_favorite = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "nav-clubes-tab"))
            )
            nav_favorite.click()

            card_padel = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "club_id_40"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", card_padel)
            time.sleep(1)
            card_padel.click()
        except Exception as e:
            print(f"An error occurred while navigating: {e}")

    def click_next_day_button(self):
        try:
            time.sleep(1.5)
            next_day = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@title="Siguiente"]'))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_day)
            time.sleep(1)
            next_day.click()
        except TimeoutException:
            print("Button not clickable within the timeout!")
        except Exception as e:
            print(f"An error occurred while clicking next day: {e}")

    def select_court(self):
        try:
            court = 287 if self.data["court"] == 1 else 288
            schedule = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f"//*[contains(@data-id, 'time-{self.data['time']}-club-40-') and contains(@data-id, '-court-{court}')]",
                    )
                )
            )

            self.driver.execute_script("arguments[0].scrollIntoView(true);", schedule)
            time.sleep(1)

            schedule.click()
        except TimeoutException:
            print("Cannot click the pitch")
        except Exception as e:
            print(f"An error occurred: {e}")

        return schedule

    def select_players(self):
        people_to_play_with = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "reservationform-name"))
        )
        people_to_play_with.click()

        for player in self.data["players"]:
            try:
                people_to_play_with.send_keys(player)

                select_player = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            ".search_result.p-2.tt-suggestion.tt-selectable",
                        )
                    )
                )

                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", select_player
                )
                time.sleep(1)

                select_player.click()

            except Exception as e:
                print(f"An error occurred while selecting player {player}: {e}")

    def accept_terms_and_reserve(self):
        try:
            terms_check_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "reservationform-terms_and_cond"))
            )
            terms_check_box.click()

            reserve = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btn_submit"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", reserve)
            time.sleep(1)
            reserve.click()

        except Exception as e:
            print(f"An error occurred during reservation: {e}")

    def monitor_schedule_class(self, schedule):
        schedule_class = schedule.get_attribute("class")
        while schedule_class != "reservaweb last":
            print("Updating...")
            time.sleep(1)
            schedule_class = schedule.get_attribute("class")

    def run(self):
        try:
            self.login()
            self.navigate_to_favorite_club()

            for _ in range(4):
                self.click_next_day_button()

            schedule = self.select_court()
            self.select_players()
            self.accept_terms_and_reserve()

            self.monitor_schedule_class(schedule)

        except (
            TimeoutException,
            NoSuchElementException,
            ElementClickInterceptedException,
            ElementNotInteractableException,
        ) as e:
            print(f"An error occurred: {e}")
        finally:
            print("Finished")
            self.driver.quit()


if __name__ == "__main__":
    driver_path = "./chromedriver-win64/chromedriver.exe"
    url = "https://www.ondepor.com/"
    keys = pd.read_csv("keys.csv", delimiter=";")

    time_wanted = "20:30"
    court = 2
    players = ["Joaquin Coviella", "Tim Bloch Bindi", "Juan Miguens"]

    data = {"time": time_wanted, "court": court, "players": players}

    bot = CourtReservationBot(driver_path, url, keys, data)
    bot.run()
