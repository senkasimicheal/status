from flask import Flask, render_template, jsonify,session
from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import secrets
from selenium import webdriver
from selenium.webdriver.edge.service import Service
import os
import stat

app = Flask(__name__, template_folder='.')
app.secret_key = secrets.token_hex(16)

car_data = []

@app.route('/')
def index():
    return render_template('results.html')

@app.route('/data')
def data():
    global car_data
    # Configure the options for Microsoft Edge
    options = EdgeOptions()
    options.use_chromium = True
    options.add_argument('--headless')
    current_directory = os.path.dirname(os.path.abspath(__file__))

    # Construct the relative file path to the WebDriver executable
    driver_path = os.path.join(current_directory, 'msedgedriver.exe')
    driver = Edge(executable_path=driver_path, options=options)
    driver.get('https://wialon.3dservices.co.ug/')
    username_field = driver.find_element(By.CSS_SELECTOR, '#user')
    password_field = driver.find_element(By.CSS_SELECTOR, '#passw')
    username_field.send_keys('micheal.coke')
    password_field.send_keys('senkasi')
    login_button = driver.find_element(By.CSS_SELECTOR, '#submit')
    login_button.click()
    
    # Wait for the page to load
    time.sleep(60)
    car_number_plates = []
    car_locations = []
    car_motion_states = []
    car_durations = []
    scrollable_element = driver.find_element(By.ID, 'monitoring_units_target_div')
    printed_car_number_plates = set()
    while True:
        car_rows = driver.find_elements(By.CSS_SELECTOR, 'tr.x-monitoring-unit-row')
        for car_row in car_rows:
            try:
                car_number_plate_element = car_row.find_element(By.CSS_SELECTOR, '[class^="monitoring_units_custom_name_"]')
                car_location_element = car_row.find_element(By.CSS_SELECTOR, '[class^="monitoring_units_location"]')
                car_motion_state_element = car_row.find_element(By.CSS_SELECTOR, '[class^="monitoring_units_state_move_"] span')
                car_motion_state = car_motion_state_element.get_attribute('class')
                car_motion_state_value = ''
                if 'red-color' in car_motion_state:
                    car_motion_state_value = 'Parked'
                elif 'green-color' in car_motion_state:
                    car_motion_state_value = 'Moving'
                elif 'icon-device-stop' in car_motion_state:
                    car_motion_state_value = 'Parked'

                car_number_plate = car_number_plate_element.text
                car_location = car_location_element.text
                if 'Cam' not in car_number_plate and car_number_plate not in printed_car_number_plates:
                    # Hover the cursor over the car_number_plate_element
                    actions = ActionChains(driver)
                    actions.move_to_element(car_number_plate_element).perform()
                    
                    try:
                        # Wait for the time information to become visible
                        wait = WebDriverWait(driver, 10)
                        wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'span.name')))

                        # Locate the td element that contains the text "ignition:" or "Ignition:"
                        td_element = driver.find_element(By.XPATH, '//td[span[@class="name" and (text()="ignition:" or text()="Ignition:")]]')

                        try:
                            # Locate the span element that contains the time information
                            time_element = td_element.find_element(By.XPATH, './/span[@class="name"]/following-sibling::span/span')

                            # Get the text content of the span element
                            time_text = time_element.text
                        except NoSuchElementException:
                            # Handle the case where the element is not found
                            time_text = "N/A"
                    except TimeoutException:
                        # Handle the case where the element is not visible within the timeout
                        print("Internet timed out")
                    printed_car_number_plates.add(car_number_plate)
                    car_number_plates.append(car_number_plate)
                    car_locations.append(car_location)
                    car_motion_states.append(car_motion_state_value)
                    car_durations.append(time_text)
                    car_data.append({
                        'number_plate': car_number_plate,
                        'location': car_location,
                        'motion_state': car_motion_state_value,
                        'duration': time_text
                    })
            except StaleElementReferenceException:
                # Element became stale, retry
                continue

        # Scroll down the div
        driver.execute_script("arguments[0].scrollBy(0, arguments[0].clientHeight)", scrollable_element)
        
        # Wait for more content to load
        time.sleep(5)

        # Check if we've reached the bottom of the div
        if driver.execute_script("return arguments[0].scrollTop + arguments[0].offsetHeight >= arguments[0].scrollHeight", scrollable_element):
            break
    # Close the driver
    driver.quit()
        
@app.route('/get_car_data')
def get_car_data():
    return jsonify(car_data)

if __name__ == '__main__':
    app.run()