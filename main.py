from pdf2image import convert_from_path
import pytesseract
import cv2
import os 
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

def initialize_folders():
    if not os.path.exists('images'):
        os.mkdir('images')
        print('images directory created!')
    
    if not os.path.exists('texts'):
        os.mkdir('texts')
        print('texts directory created!')

def convert_pdf_to_image(file_name, pdf_path):
    try:
        images = convert_from_path(pdf_path)
        folder_name = 'images'
        base_name = file_name

        image_list = []

        for i in range(len(images)):
            image_name = f'./{folder_name}/{base_name}-page{i}.jpg'
            image_list.append(image_name)
            images[i].save(image_name, 'JPEG')

        print('converted to images!')

    except:
        print('error converting images')

    return image_list

def extract_text_from_image(image_path):
    img = cv2.imread(image_path)

    text = pytesseract.image_to_string(img)

    return text

def save_text_to_file(file_name, text):
    try:
        print(text)
        file = open(f'./texts/{file_name}.txt', 'w')
        file.write(text)
        
    except:
        print('error saving text!')

def list_files(folder_path):
    files = os.listdir(folder_path)

    return files

def sort_by_page(file_name):
    page = os.path.splitext(file_name)[0]
    page_number = page[9:]
   
    return int(page_number)

def problems_page(text):
    lines = text.splitlines()
    search1 = 'Solutions to Non-Starred Exercises'
    search2 = 'Solution to Non-Starred Exercises'
    pages = []
    for content in lines:
        if search1 in content or search2 in content:
            print(content)
            page = int(content.split()[-1]) - 5 + 30 # 30 is page 1, 5 pages before the search are the problems
            pages.append(page)

    return pages

def problem_page_number_to_problems(images, page):
    text = ''
    page_upper = 5
    for i in range(page-1, page + page_upper + 1):
        text += extract_text_from_image('images/' + images[i])

    lines = text.splitlines()
    search1 = 'Kattis'
    search2 = 'Extra Kattis'
    search3 = 'Entry Level: Kattis'
    problems = []
    for content in lines:
        if search2 in content:
            problems.extend(content.split()[2:])
        elif search3 in content:
            content = content.split()
            if content[5] == '*':
                problems.append(content[6])
            else:
                problems.append(content[5])
        elif search1 in content:
            content = content.split()
            if content[2] == '-':
                problems.append(content[3])
            else: 
                problems.append(content[2])
    
    return problems

def export_to_sheets(df):
    try:
        sa = gspread.service_account(filename='kattis-390005-b3ee517ded4d.json')
        kattis_spreadsheet = sa.open('Kattis Problems')
        
        # Select first sheet
        worksheet = kattis_spreadsheet.sheet1
        
        # Save to sheet
        data = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(data)            
        
        print('successfully saved to sheet!')
        print(kattis_spreadsheet.url)
    except Exception as e:
        print('error saving to sheet:', str(e))

def convert_to_df(problems):
    try:
        # Clean problems
        new_problems = [None] * len(problems)
        for i in range(len(problems)):
            if not problems[i][-1].isalpha():
                new_problems[i] = problems[i][:-1]
            else:
                new_problems[i] = problems[i]
     
        # Add links
        base_url = 'https://open.kattis.com/problems/'
        links_to_problems = [None] * len(new_problems)
        for i in range(len(new_problems)):
            links_to_problems[i] = base_url + new_problems[i]
    
        # Add Status
        statuses = ['Not Solved'] * len(new_problems)

        # Transform to datafram
        df = pd.DataFrame({
            'Problem': new_problems,
            'Link': links_to_problems,
            'Status': statuses 
            })
        
        return df
    except:
        print('error converting to df')
       
def main():
    initialize_folders()

    file_name = 'book'
    file_path = './book.pdf'

    # images = convert_pdf_to_image(file_name, file_path)
    images = list_files('images')
    images_sorted = sorted(images, key=sort_by_page)

    # Extract Table of Contents to get the Pages of the Problem Set
    table_of_contents = ''
    for i in range(2, 5):
        img = 'images/' + images_sorted[i]
        table_of_contents += extract_text_from_image(img)

    problems_pages = problems_page(table_of_contents)
    problems = []
    for page in problems_pages:
        problems.extend(problem_page_number_to_problems(images_sorted, page))
        
    df = convert_to_df(problems)
    export_to_sheets(df)
    
if __name__ == '__main__':
    main()