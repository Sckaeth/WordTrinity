import unittest, os, time, uuid
from app import app, db
from app.models import User, Word, Puzzle, Game
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from app.api import words, load

basedir = os.path.abspath(os.path.dirname(__file__))

class SystemTest(unittest.TestCase):
    driver = None

    def setUp(self):
        # Create a new Firefox session
        self.driver = webdriver.Firefox(executable_path=os.path.join(basedir,'geckodriver'))

        db.init_app(app)
        db.create_all()
        db.session.commit()

        words.populate_database()

        if not self.driver:
            self.skipTest('Web browser not available')
        else:
            self.driver.implicitly_wait(30)
            self.driver.maximize_window()
            # Navigate to the application home page
            self.driver.get("http://localhost:5000")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.driver.quit()

    def test_puzzle_win(self):
        # Database
        puzzle = Puzzle.query.filter_by(puzzleid=load.get_current_puzzleid()).first()
        word1 = Word.query.filter_by(wordid=puzzle.wordid1).first().wordname
        word2 = Word.query.filter_by(wordid=puzzle.wordid2).first().wordname
        word3 = Word.query.filter_by(wordid=puzzle.wordid3).first().wordname

        # Elemeents
        time.sleep(2)
        submit_word = self.driver.find_element(By.ID,'submit-word')
        submit_puzzle = self.driver.find_element(By.ID,'submit-puzzle')
        action = webdriver.ActionChains(self.driver)
        rotate = self.driver.find_element(By.ID,'shift-right')

        # Guess letters with keyboard
        action.send_keys(word1, Keys.ENTER, Keys.SPACE).perform()

        # Check turns remaining
        turns = self.driver.find_element(By.CLASS_NAME, 'puzzle__counter')
        self.assertEqual(turns.get_attribute('innerText'), 'TURNS REMAINING: 9', msg='Puzzle succesfully registers keyboard input.')
        
        # Test incorrect letter
        slot = self.driver.find_element(By.CSS_SELECTOR, '#word-2 > :nth-child(2)')
        slot.click()
        action.send_keys('0').perform()
        self.assertEqual(slot.get_attribute('innerText'), '', msg='Puzzle successfully rejects incorrect keyboard input.')

        # Guess letters with mouse
        letter = self.driver.find_element(By.CSS_SELECTOR, '.puzzle__letters > :enabled')
        letter.click()
        self.assertEqual(letter.get_attribute('innerText'), slot.get_attribute('innerText'), msg='Letter click successfully added letter to slot.')
        action.send_keys(Keys.BACKSPACE, word2).perform()

        # Submit and rotate with mouse
        submit_word.click()
        rotate.click()

        # Test submit with incorrect input
        action.send_keys(word3, Keys.BACKSPACE).perform()
        submit_word.click()
        self.assertEqual(turns.get_attribute('innerText'), 'TURNS REMAINING: 8', msg='Successfully rejected invalid submit input.')

        # Submit all
        reset = self.driver.find_element(By.ID, 'reset-letters')
        reset.click()
        time.sleep(1)
        action.send_keys(word3).perform()
        submit_puzzle.click()
        time.sleep(2)

        # Result
        self.assertEqual(turns.get_attribute('innerText'), 'GAME WON', msg='Successfully won game.')

        # Check game stats
        guesses = self.driver.find_element(By.CSS_SELECTOR, '.user-guesses')
        self.assertEqual(guesses.get_attribute('innerText'), '3', msg='Successfully updated statistics.')

    def test_puzzle_loss(self):
        # Database
        puzzle = Puzzle.query.filter_by(puzzleid=load.get_current_puzzleid()).first()
        word1 = Word.query.filter_by(wordid=puzzle.wordid1).first().wordname
        word2 = Word.query.filter_by(wordid=puzzle.wordid2).first().wordname
        word3 = Word.query.filter_by(wordid=puzzle.wordid3).first().wordname

        # Send input
        time.sleep(2)
        action = webdriver.ActionChains(self.driver)
        action.send_keys(word3, Keys.ENTER, Keys.SPACE, word1, Keys.ENTER, Keys.SPACE, word2).perform()
        submit_puzzle = self.driver.find_element(By.ID,'submit-puzzle')
        submit_puzzle.click()

        # Result
        time.sleep(3)
        turns = self.driver.find_element(By.CLASS_NAME, 'puzzle__counter')
        self.assertEqual(turns.get_attribute('innerText'), 'GAME OVER', msg='Successfully lost game.')

    def test_change_user(self):
        # Database
        userid = str(uuid.uuid4()).replace("-","")
        user = User(userid=userid)
        db.session.add(user)
        db.session.commit()
        puzzle = Puzzle.query.filter_by(puzzleid=load.get_current_puzzleid()).first()
        word1 = Word.query.filter_by(wordid=puzzle.wordid1).first().wordname
        word2 = Word.query.filter_by(wordid=puzzle.wordid2).first().wordname
        word3 = Word.query.filter_by(wordid=puzzle.wordid3).first().wordname

        # Find stats
        stats_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-bs-show="#stats"]')
        winrate = self.driver.find_element(By.CSS_SELECTOR, '.user-winrate')
        close_stats = self.driver.find_element(By.CSS_SELECTOR, '.modal-header-bg > button')

        # Use a turn, should return win game
        time.sleep(2)
        action = webdriver.ActionChains(self.driver)
        action.send_keys(word1, Keys.ENTER, Keys.SPACE, word2, Keys.ENTER, Keys.SPACE, word3, Keys.ENTER).perform()
        time.sleep(2)
        self.assertEqual(winrate.get_attribute('innerText'), '100', msg='Succesfully loaded stats')
        time.sleep(2)

        # Find account elements
        modal = self.driver.find_element(By.CSS_SELECTOR, '[data-bs-show="#account"]')
        modal.click()
        change_user_btn = self.driver.find_element(By.ID,'change-user')
        change_user_field = self.driver.find_element(By.ID,'new-userid')
        current_user = self.driver.find_element(By.CSS_SELECTOR, '.account__userid > span')
        initial = current_user.get_attribute('innerText')

        # New user ID with invalid ID
        time.sleep(1)
        change_user_field.send_keys('aa')
        change_user_btn.click()
        time.sleep(2)
        self.assertEqual(current_user.get_attribute('innerText'), initial, msg='Successfully detected invalid user ID')
        change_user_field.clear()

        # New user ID with valid ID
        change_user_field.send_keys(userid)
        change_user_btn.click()
        time.sleep(2)
        self.assertEqual(current_user.get_attribute('innerText'), userid, msg='Successfully changed user ID')

        # Check if puzzle turns reloaded
        turns = self.driver.find_element(By.CLASS_NAME, 'puzzle__counter')
        self.assertEqual(turns.get_attribute('innerText'), 'TURNS REMAINING: 10', msg='Succesfully reloaded puzzle')

        # Check if stats reloaded
        stats_btn.click()
        self.assertEqual(winrate.get_attribute('innerText'), '0', msg='Succesfully reloaded stats')

if __name__ == '__main__':
    unittest.main() 