import os
import glob
import base64
import numpy as np
import pandas as pd
import pdfplumber
import re



from PIL import Image
from io import BytesIO
from pdfminer.pdfparser import PSSyntaxError
from src.start_page_utils import (crop_borders,
                               to_subscript_formula,
                               get_first_page_details,
                            #    get_structure_img,
                               merge_compund_section,
                               process_compounds_section,
                               merge_approval_section)

from src.appearance_utils import (find_appearance_block,
                                extract_description)

from src.last_page_utils import get_footer_dict, get_last_page_data

from src.revision_history_utils import extract_revision_history


formula = "C23H23ClFNO5"
formatted_formula = to_subscript_formula(formula)

def extract_from_document(file):
    pdf = pdfplumber.open(file)

    test_page = pdf.pages[0]
    test_page  = crop_borders(test_page, pdf)
    test_text = test_page.extract_text()
    if test_text:

        #### For TOP section in First page
        first_pg_top_sec_dict = get_first_page_details(pdf)
        first_pg_top_sec_df = pd.DataFrame([first_pg_top_sec_dict])
        
        #### For Chemical Structure
        # structure_img = get_structure_img(pdf)
        # buffered = BytesIO()
        # structure_img.save(buffered, format="PNG")
        # img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        # structure_df = pd.DataFrame({'Image': [img_str]})

        #### For CENTER section in First page
        page = pdf.pages[0]
        rows = page.extract_table(table_settings={"horizontal_strategy": "lines"})

        compounds_section = rows[0][0]
        #approvals_section = rows[1]

        ### For Compunds section in First page
        comp_lines = compounds_section.split("\n") # If comp_lines is empty
        comp_lines = merge_compund_section(comp_lines)
        first_pg_center_sec_dict = process_compounds_section(comp_lines)
        # Removes duplicates from topsection and centersection of page1
        first_pg_dict = {**first_pg_top_sec_dict, **first_pg_center_sec_dict}
        first_pg_center_sec_df = pd.DataFrame([first_pg_dict])


        ### For Approval section in First Page
        # first_pg_approvls_sec_df = merge_approval_section(approvals_section)

        #### For APPEARANCE section in Later pages
        appearance_df = find_appearance_block(pdf)

        #### For Description Section in Later pages
        for page in pdf.pages:
            page  = crop_borders(page, pdf)
            text = page.extract_text()
            if "DESCRIPTION" in text:
                description_text = extract_description(page)
        description_df = pd.DataFrame([description_text], columns=["Description"])

        def extract_parts(description):
            # Regex pattern to match part numbers (e.g., GS-9132, PC-11031, etc.)
            pattern = r'(\b[A-Z]{1,2}-\d{4,5}\b)'
            parts = re.split(pattern, description)
            
            result = []
            for i in range(1, len(parts), 2):
                part_number = parts[i]
                desc = parts[i + 1].strip()
                result.append([part_number, desc])
            
            return result

    # Apply the function and create a new DataFrame
        extracted_data = []
        for desc in description_df['Description']:
            extracted_data.extend(extract_parts(desc))

    # Create a new DataFrame from the extracted data
        new_df = pd.DataFrame(extracted_data, columns=['Part Number', 'Description'])







        #### For Revision history in Later pages
        final_layout_text = extract_revision_history(pdf)


        final_layout_text_df = pd.DataFrame([final_layout_text], columns=["Revision History"])
        
   
        final_layout_text_df = pd.DataFrame(final_layout_text_df)
        #print(final_layout_text_df)


        #start

        def extract_parts(description):
            # Regex pattern to match revision and author
            pattern = r'(\d{4}\.\d{2})\s+(\b[A-Z]\. [A-Z][a-zA-Z]*\b)([^\d]*)'
            matches = re.findall(pattern, description)
            
            result = []
            for match in matches:
                revision, author, desc = match
                desc = desc.strip()  # Remove any leading/trailing whitespace from description
                result.append([revision, author.strip(), desc.strip()])
            
            return result

    # Apply the function and create a new DataFrame
        all_extracted_data = []
        for text in final_layout_text_df['Revision History']:
            all_extracted_data.extend(extract_parts(text))
        
        new_df1 = pd.DataFrame(all_extracted_data, columns=['Revision', 'Author','Description'])








        #### For Footer in all pages
        footer = pdf.pages[0].crop((0, 700, pdf.pages[0].width, pdf.pages[0].height))
        footerlines = footer.extract_text_simple().split("\n")
        footer_data = get_footer_dict(footerlines)
        footer_df = pd.DataFrame([footer_data])

        #### For Data in Last pages
        last_pg_df  = get_last_page_data(pdf)

        final_result_df = pd.concat([
                                    # first_pg_top_sec_df,
                                    # structure_df, 
                                    first_pg_center_sec_df,
                                    # first_pg_approvls_sec_df,
                                    appearance_df,
                                    new_df,
                                    #final_layout_text_df,
                                    new_df1,
                                    footer_df,
                                    last_pg_df
                                    ], axis=1)
        # return structure_img, final_result_df
        return final_result_df
    else:
        return None

if __name__=="__main__":
    for file in glob.glob(r"D:\Purna_Office\Soulpage_New\Task-50_0_GILEAD\Extended_POC_2\*.pdf"):
        file_name = os.path.basename(file)
        excel_file_name = file_name.split(".")[0]+".xlsx"
        structure_file_name = file_name.split(".")[0]+".png"
        print(file_name)

        if file_name.startswith("SPEC"):
            try:
                result_df = extract_from_document(file)
                if result_df is not None:
                    result_df.to_excel(excel_file_name)
                    # structure_img.save(structure_file_name)
            except PSSyntaxError as e:
                print(f"PSSyntaxError occurred while processing file {file}: {e}")
            except Exception as e:
                print(f"An error occurred while processing file {file}: {e}")     
