import os
import pdfplumber
import numpy as np
import pandas as pd
from PIL import Image
import re
# from decimer_segmentation import segment_chemical_structures


def crop_borders(page, pdf):
    return page.within_bbox((30,30,pdf.pages[0].width-30, 700))

def to_subscript_formula(formula):
    # Dictionary to map numbers to their subscript characters
    subscript_map = {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'
    }
    
    # Convert the formula to subscript
    subscript_formula = ""
    for char in formula:
        if char.isdigit():
            subscript_formula += subscript_map[char]
        else:
            subscript_formula += char
            
    return subscript_formula

def merge_compund_section(lines):
    merged_lines = []
    for line in lines:
        if ':' not in line and merged_lines:
            merged_lines[-1] += ' ' + line.strip()
        else:
            merged_lines.append(line.strip())

    return merged_lines


def merge_approval_section(apprv_list):
    total_approvals = []
    for line in apprv_list:
        item_dict = {}
        lines = line.split("\n")
        item_dict[lines[0]] = " by ".join(lines[1:])
        total_approvals.append(item_dict)
    total_approvals_df = pd.DataFrame(total_approvals)
    return total_approvals_df

def process_compounds_section(lines):
    item_dict = {}
    for line in lines:
        # print("Line:", line)
        key,value = line.split(":")
        item_dict[key] = value
    
    return item_dict


# def get_structure_img(pdf):
#     page1  = pdf.pages[0].to_image()
#     page1  = np.array(page1.original)
#     segments = segment_chemical_structures(page1, expand= True)
#     # segments = segment_chemical_structures_from_file(file_path, expand=True, poppler_path=None)
#     if segments:
#         # Show first segment
#         img = Image.fromarray(segments[0])
#         return img
#     else:
#         # create blank image
#         img = np.zeros([100,100,3],dtype=np.uint8)
#         img.fill(255) # or img[:] = 255
#         img = Image.fromarray(img)
#         return img

def get_first_page_details(pdf):
    text = pdf.pages[0].extract_text(y_tolerance=6, x_tolerance=6)
    sample_dict = {}

    for row in text.split("\n"):
        if ":" in row:
            try:
                key, val = row.split(":")
                if len(key.strip()) > 1 and len(val.strip()) > 1:
                    sample_dict[key.strip()] = val.strip()
            except Exception as e:
                print(f"Error processing row: {row}. Error: {e}")

    for key in sample_dict:
        val = sample_dict[key]
        if key == 'MOLECULAR WEIGHT':
            val = re.sub(r'\b[A-Z]+\s+\d+\b', '', val).strip()
        else:
            val = re.sub(r'[A-Z\s]+$', '', val).strip()

        sample_dict[key] = val  # Update the value in sample_dict

    return sample_dict


if __name__=="__main__":
    file = "D:\Purna_Office\Soulpage_New\Task-50_0_GILEAD\Extended_POC_2\SPEC-0012 Elvitegravir Drug Substance.pdf"
    pdf = pdfplumber.open(file)

    df = get_first_page_details(pdf)
    structure = get_structure_img(pdf)

    page = pdf.pages[0]
    rows = page.extract_table(table_settings={"horizontal_strategy": "lines"})
    
    compounds_section = rows[0][0]
    approvals_section = rows[1]

    # compunds section
    comp_lines = compounds_section.split("\n")
    # print("Comp", comp_lines)
    comp_lines = merge_compund_section(comp_lines)
    result = process_compounds_section(comp_lines)
    
    # approval sections
    result1 = merge_approval_section(approvals_section)
    # print(result)
    print(df)
