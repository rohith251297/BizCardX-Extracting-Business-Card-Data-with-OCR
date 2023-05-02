import easyocr as ocr  # OCR
import streamlit as st  # Web App
from PIL import Image  # Image Processing
import numpy as np  # Image Processing
import re
import mysql.connector as con
import io
png = "https://www.nicepng.com/png/detail/182-1826178_my-business-card-line-comments-visiting-card-icon.png"
st.set_page_config(page_title="BIZCARD-X", page_icon=png)

# Connect to mysql
connector = con.connect(
    host="localhost",
    user="root",
    password='123456'
     )
cursor = connector.cursor()

cursor.execute('CREATE database IF NOT EXISTS Business_card')

connector = con.connect(
    host= "localhost",
    user = "root",
    password = '123456',
    database = 'Business_card'
     )
cursor = connector.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS card 
              (id INT AUTO_INCREMENT PRIMARY KEY,
              card_holder_details TEXT,
              address TEXT,
              pin_code VARCHAR(25),
              phone_numbers VARCHAR(25),
              email TEXT,
              website_url TEXT
              )''')

# title
st.title(":orange[Extracting Business Card Data with OCR]")

menu = ['Upload Data', 'View and Delete', 'About']
choose = st.sidebar.selectbox("Select An Option", menu)

if choose == 'Upload Data':
    st.write("### :red[ UPLOAD ANY BUSINESS CARD IMAGE TO EXTRACT INFORMATION] ")
    CD, col1, col2, col3 = st.columns([0.5, 4, 1, 4])
    with col1:
        # image uploader
        st.write("#### SELECT IMAGE")
        image = st.file_uploader(label="", type=['png', 'jpg', 'jpeg'])


    @st.cache_data
    def load_model():
        reader = ocr.Reader(['en'])
        return reader


    reader = load_model()  # load model
    if image is not None:
        input_image = Image.open(image)  # read image
        with col1:
            st.image(input_image)  # display image
            st.write(" ")

        result = reader.readtext(np.array(input_image))
        result_text = []  # empty list for results
        for text in result:
            result_text.append(text[1])

        PH = []
        PHID = []
        ADD = set()
        AID = []
        EMAIL = ''
        EID = ''
        PIN = ''
        PID = ''
        WEB = ''
        WID = ''

        for i, string in enumerate(result_text):
            # st.write(string.lower())

            # TO FIND EMAIL
            if re.search(r'@', string.lower()):
                EMAIL = string.lower()
                EID = i

            # TO FIND PINCODE
            match = re.search(r'\d{6,7}', string.lower())
            if match:
                PIN = match.group()
                PID = i

            # TO FIND PHONE NUMBER
            # match = re.search(r'(?:ph|phone|phno)?(?:[+-]?\d*){7,}', string)
            # match = re.search(r'(?:ph|phone|phno)?\s*(?:[+-]?\d\s*){7,}', string)
            match = re.search(r'(?:ph|phone|phno)?\s*(?:[+-]?\d\s*[\(\)]*){7,}', string)
            if match and len(re.findall(r'\d', string)) > 7:
                PH.append(string)
                PHID.append(i)

            # TO FIND ADDRESS
            keywords = ['road', 'floor', ' st ', 'st,', 'street', ' dt ', 'district',
                        'near', 'beside', 'opposite', ' at ', ' in ', 'center', 'main road',
                        'state', 'country', 'post', 'zip', 'city', 'zone', 'mandal', 'town', 'rural',
                        'circle', 'next to', 'across from', 'area', 'building', 'towers', 'village',
                        ' ST ', ' VA ', ' VA,', ' EAST ', ' WEST ', ' NORTH ', ' SOUTH ']
            # Define the regular expression pattern to match six or seven continuous digits
            digit_pattern = r'\d{6,7}'
            # Check if the string contains any of the keywords or a sequence of six or seven digits
            if any(keyword in string.lower() for keyword in keywords) or re.search(digit_pattern, string):
                ADD.add(string)
                AID.append(i)

            # TO FIND STATE (USING SIMILARITY SCORE)
            states = ['Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat',
                      'Haryana', 'Hyderabad', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh',
                      'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
                      'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
                      'West Bengal',
                      "United States", "China", "Japan", "Germany", "United Kingdom", "France", "India",
                      "Canada", "Italy", "South Korea", "Russia", "Australia", "Brazil", "Spain", "Mexico", 'USA', 'UK']

            import Levenshtein


            def string_similarity(s1, s2):
                distance = Levenshtein.distance(s1, s2)
                similarity = 1 - (distance / max(len(s1), len(s2)))
                return similarity * 100


            for x in states:
                similarity = string_similarity(x.lower(), string.lower())
                if similarity > 50:
                    ADD.add(string)
                    AID.append(i)

            # WEBSITE URL
            if re.match(r"(?!.*@)(www|.*com$)", string):
                WEB = string.lower()
                WID = i
        with col3:
            # DISPLAY ALL THE ELEMENTS OF BUSINESS CARD
            st.write("#### EXTRACTED TEXT")
            st.write('##### :blue[WEBSITE URL: ] ' + str(WEB))
            st.write('##### :blue[EMAIL: ] ' + str(EMAIL))
            st.write('##### :blue[PIN CODE: ] ' + str(PIN))
            ph_str = ', '.join(PH)
            st.write('##### :blue[PHONE NUMBER(S): ] ' + ph_str)
            add_str = ' '.join([str(elem) for elem in ADD])
            st.write('##### :blue[ADDRESS: ] ', add_str)

            IDS = [EID, PID, WID]
            IDS.extend(AID)
            IDS.extend(PHID)
            #         st.write(IDS)
            oth = ''
            fin = []
            for i, string in enumerate(result_text):
                if i not in IDS:
                    if len(string) >= 4 and ',' not in string and '.' not in string and 'www.' not in string:
                        if not re.match("^[0-9]{0,3}$", string) and not re.match("^[^a-zA-Z0-9]+$", string):
                            numbers = re.findall('\d+', string)
                            if len(numbers) == 0 or all(len(num) < 3 for num in numbers) and not any(
                                    num in string for num in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] * 3):
                                fin.append(string)
            st.write('##### :blue[CARD HOLDER & COMPANY DETAILS: ] ')
            for i in fin:
                st.write('##### ' + i)

            UP = st.button('UPLOAD TO DATABASE', key=90)

        # DATABASE CODE
        website = str(WEB)
        email = str(EMAIL)
        pincode = str(PIN)
        phoneno = ph_str
        address = add_str
        det_str = ' '.join([str(elem) for elem in fin])
        details = det_str
        image.seek(0)
        image_data = image.read()

        # IF UPLOAD BUTTON IS ON, THE DATA IS UPLOADED TO DATABASE
        if UP:
            if image is not None:
                # Read image data
                # Insert image data into MySQL database
                data = (website, email, pincode, phoneno, address, details)
                sql = "INSERT INTO card (website_url, email, pin_code, phone_numbers, address, card_holder_details) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, data)
                connector.commit()
            else:
                st.write('Please upload business card')
    st.write(' ')
    st.write(' ')

    
elif choose == 'View and Delete':
    # DATABASE PART
    st.write('### EXPLORE BUSINESS CARDS DATABASE ')
    cd, c1, c2, c3 = st.columns([0.5, 4, 1, 4])
    with c1:
        st.write(' ')
        st.write("#### BUSINESS CARDS AVAILABLE IN DATABASE")
        cursor.execute("SELECT id FROM card")
        rows = cursor.fetchall()
        l = []
        # DISPLAY ALL THE CARDS AS BUTTONS
        for row in rows:
            l.append(row[0])
            button_label = f"SHOW BUSINESS CARD: {row[0]}"
            if st.button(button_label):
                cursor.execute("SELECT * FROM card WHERE id =" + str(row[0]))
                row1 = cursor.fetchone()
                website_url = row1[1]
                email = row1[2]
                pin_code = row1[3]
                phone_numbers = row1[4]
                address = row1[5]
                card_holder_details = row1[6]

                # DISPLAY SELECTED CARD DETAILS
                with c3:
                    st.write(f"#### BUSINESS CARD {row[0]} DETAILS ")
                    st.write(f"Website: {website_url}")
                    st.write(f"Email: {email}")
                    st.write(f"PIN Code: {pin_code}")
                    st.write(f"Phone Numbers: {phone_numbers}")
                    st.write(f"Address: {address}")
                    st.write(f"Card Holder & Company Details: {card_holder_details}")



    # DELETE MULTIPLE ENTRIES
    with c1:
        st.write(' ')
        st.write(f"#### SELECT ENTRIES TO DELETE")
        selected_options = st.multiselect('', l)

        if st.button('DELETE SELECTED ENTRIES'):
            for option in selected_options:
                cursor.execute("DELETE FROM card WHERE id = " + str(option))
            connector.commit()
            st.write("DELETED SELECTED BUSINESS CARD ENTRIES SUCCESSFULLY")
        st.write(' ')

elif choose == 'About':
    st.title(":red[BIZCARD-X:star:]")
    st.image("https://gkmockups.com/wp-content/uploads/2019/05/BusCard_Ort_Animation.gif", width=600)
    st.write('')
    st.write('')
    st.write('''it was developed with a Streamlit application that allows users to
            upload an image of a business card and extract relevant information from it using
            easyOCR. The extracted information should include the company name, card holder
            name, designation, mobile number, email address, website URL, area, city, state,
            and pin code. The extracted information should then be displayed in the application's
            graphical user interface (GUI).
            In addition, the application should allow users to save the extracted information into
            a database along with the uploaded business card image. The database should be
            able to store multiple entries, each with its own business card image and extracted
            information.''')
