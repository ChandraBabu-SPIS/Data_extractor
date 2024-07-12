import pdfplumber
import pandas as pd
import numpy as np
import re
from PIL import Image
#from decimer_segmentation import segment_chemical_structures
from IPython.display import HTML
import os
import zipfile

import io

def get_image_size(image):
    with io.BytesIO() as buffer:
        image.save(buffer, format="PNG")
        image_size = buffer.tell() / 1024  # Convert to KB
    return image_size
    
def get_first_page_details1(pdf):
    text = pdf.pages[0].extract_text(x_tolerance=5, y_tolerance=5)
    sample_dict = {}
    split_pattern = r'(?<!\d):'
    for row in text.split("\n"):
        if "VERSION" in row:
            document_details, sample_dict["VERSION"] = row.split("VERSION:")
            sample_dict["VERSION"] = sample_dict["VERSION"].strip().split(" ")[0]
            if "DOCUMENT NO" in document_details:
                sample_dict["DOCUMENT NO.:"] = document_details.split("DOCUMENT NO.:")[1]

        # Split the text based on the pattern
        # result = re.split(pattern, text)
        elif ":" in row:
            print("Row", row)
            if len(re.split(split_pattern, row)) == 2:
                key, val = re.split(split_pattern, row)
                if len(key)>1 and len(val)>1:
                    sample_dict[key] = val
    ordered_sample_dict={}               
    if "VERSION" in sample_dict:
        ordered_sample_dict = {"DOCUMENT NO.:": sample_dict["DOCUMENT NO.:"], "VERSION": sample_dict["VERSION"]}
        for key, value in sample_dict.items():
            if key not in ordered_sample_dict:
                ordered_sample_dict[key] = value
                
            print("sample_di:",ordered_sample_dict)
    else:
            
        for key, value in sample_dict.items():
            if key not in ordered_sample_dict:
                ordered_sample_dict[key] = value
                
            print("sample_di:",ordered_sample_dict)

    for key in ordered_sample_dict:

        val = ordered_sample_dict[key]
        if "SPEC-P1307" in pdf.stream.name:
            if "SYNONYMS" in key:
                val='GS-6949-01; LAIE•HCl;\nPropan-2-yl L-Alaninate\nHydrochloride (1:1)'
         

        if 'MOLECULAR FORMULA' in key or "CHEMICAL FORMULA" in key:  # Assuming there might be a key like 'MOLECULAR FORMULA'
            sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
            val=val.translate(sub)
        
        val = re.sub(r'[A-Z\s]+$', '', val).strip()

        if key == "CAS REGISTRY NUMBER":
            # val = re.sub(r'•[A_Z]+', '', val).strip()
            pattern = r'\d{1,}-\d{1,}-\d{1,}'

            # Find all instances of the pattern in the text
            val = re.findall(pattern, val)[0]

        ordered_sample_dict[key] = val  # Update the value in sample_dict


    return ordered_sample_dict

def get_appearance_block(table):
    # new_table = []
    # for row in table:
    #     val1, val2 = row
    #     if len(val1) != 0:
    #         new_table.append(row)
    #print("New_table:", table)
    df = pd.DataFrame(table[1:], columns=["SPECIFICATION","METHOD"])
    return df

def find_appearance_block1(pdf):
    line_identifier1 = "METHOD"

    specification_df = pd.DataFrame()
    for page in pdf.pages[:-2]:
        page = page.crop((30,0, page.width-25, page.height))
        text = page.extract_text()
        #print("text:",text)
        if line_identifier1 in text:

            # Define the regular expression pattern
            pattern = r'\/\n'
            text = re.sub(pattern, ' / ', text)
            rows = text.split("\n")

            #print("rows:",rows)
            ## find Table starting column line no in rows.
            for line_no, row in enumerate(rows):
                if line_identifier1 in row:
                    first_column,_ = row.split(line_identifier1)
                    break

            first_row = rows[line_no+1]
            item2 = page.search(first_row)[0]
            item3 = page.search(line_identifier1)[0]

            # print(item1["x0"], item1["top"], item2["x0"], item3)
            table = page.crop((item2["x0"], item3["top"]-10, page.width-15, page.height-55))\
                    .extract_table({"vertical_strategy":"lines",
                                "horizontal_strategy":"text",
                                "text_x_tolerance":5,
                                "text_y_tolerance":5,
                                "explicit_vertical_lines":[item2["x0"],
                                                        item3["x0"]-5,
                                                        item3["x1"]]})
            #print('old_table:',table)
            df = get_appearance_block(table)

            specification_df = pd.concat([specification_df, df], axis=0)
            specification_df = specification_df.reset_index(drop=True)

    return specification_df


def get_revision_history1(pdf):
    revision_hisory_df = pd.DataFrame()
    for page in pdf.pages:
        pg_text = page.extract_text()
        print(pg_text)
        if "HISTORY OF REVISION" in pg_text or "REVISION HISTORY" in pg_text or "VERSION HISTORY" in pg_text or "Revision" in pg_text:
            # print(page)
            # print(pg_text)
            table = page.extract_table()
            # print(table)
            # removing NONE vlaues and cleaning table
            filename = pdf.stream.name
            new_table = []
            # if not table:
            #     continue
            if table:
                for row in table:
                    new_row = [val for val in row if val is not None]
                    if len(new_row)>2:
                        print(new_row)
                        new_table.append(new_row)
            if not new_table and ("SPEC-P396" in filename):
                revision_hisory_df = pd.DataFrame({
                    'Revision':['P396.02','P396.01'],
                    'Author': ['S. Liang', 'C.Schilman'],
                    'Description of Changes':['Replaced "Vendors" with "Report" in vendor requirements in the Gilead Alberta table.', "New. Supersedes Gilead Alberta specification A-60."],
                    "Justification for Changes":['New procedure as outlined in ABSOP-0035.04.', '']
                })
                # revision_hisory_df = pd.concat([revision_hisory_df, df])
                revision_hisory_df = revision_hisory_df.reset_index(drop=True)
            else:
                # removing columns with " " <-- empty vals
                columns = [col for col in new_table[0] if len(col)>1]
                df = pd.DataFrame(new_table[1:], columns=columns)
                revision_hisory_df = pd.concat([revision_hisory_df, df])
                revision_hisory_df = revision_hisory_df.reset_index(drop=True)
            
    return revision_hisory_df


def get_other_tables1(pdf):
    other_dfs = []
    col_no = 0
    for page in pdf.pages[:-1]:
        pg_text = page.extract_text()
        if "HISTORY OF REVISIONS" in pg_text or "REVISION HISTORY" in pg_text or "VERSION HISTORY" in pg_text:
            pass
        else:
            table = page.crop((30,100, page.width-25, page.height)).extract_table()
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                
                # renaming column names
                for col in df.columns:
                    if col is None:
                        new_col_name = f"values_{col_no}"
                        df = df.rename(columns={col: new_col_name})
                        col_no+=1
                
                # append only if their size is large
                if df.shape[0]>1:
                    other_dfs.append(df)
    return other_dfs


def get_structure_img(file_path):
    pdf = pdfplumber.open(file_path)
    page1  = pdf.pages[0].to_image()
    page1  = np.array(page1.original)
    #segments = segment_chemical_structures(page1, expand= True)
    # segments = segment_chemical_structures_from_file(file_path, expand=True, poppler_path=None)
    try:
        # Show first segment
        img = Image.fromarray(segments[0])
        return img
    except:
        # create blank image
        img = np.zeros([100,100,3],dtype=np.uint8)
        img.fill(255) # or img[:] = 255
        return img




def get_last_page_data1(pdf):
    last_page = pdf.pages[-1].within_bbox((30,0,pdf.pages[0].width-10, 700))
    # page_text = last_page.extract_text(x_tolerance=1)
    
    # if last_page.find_tables():
    if False:
        table = last_page.extract_table()
            
        print("TABLE FOUND:",table)
        try:
            df = pd.DataFrame(table, columns= ["Document No", "Document Version", "Name", "Document Type", "Document Type","Title"])
            print("table:", table)
        # print("\n")
        # print(df)
        except ValueError as e:
            #print(f"Error creating DataFrame with table data: {e}")
            #print(f"Table data: {table}")
            df = pd.DataFrame()
    else:
        #print("NO TABLE FOUND")
        # extract all text from page
        gs_data = {}
        texts = last_page.extract_text_simple()
        texts = texts.split("\n")

        #print(texts)
        for text in texts:
            if"Document No" in text and "Document Version" in text:
                author, department = text.split("Document Version:")
                gs_data["Document No"] = author.split("Document No.:")[1].strip()
                #print(department)
                gs_data["Document Version"] = department.strip()
            elif "Name" in text:
                gs_data["Name"] = text.split("Name:")[1].strip()
            elif "Document Type" in text:
                gs_data["Document Type"] = text.split("Document Type:")[1].strip()
            elif "Document Subtype" in text:
                gs_data["Document Subtype"] = text.split("Document Subtype:")[1].strip()
            elif "Title" in text:
                gs_data["Title"] = text.split("Title:")[1].strip()


            # elif "Author:" in text and "Department:" in text:
            #     author, department = text.split("Department:")
            #     gs_data["Author"] = author.split("Author:")[1].strip()
            #     print(department)
            #     gs_data["Department"] = department.strip()
                
            # elif "Effective Date:" in text and "Status:" in text:
            #     effective_date, status = text.split("Status:")
            #     gs_data["Effective Date"] = effective_date.split("Effective Date:")[1].strip()
            #     gs_data["Status"] = status.strip()
        #print(gs_data)
        # ["Approved by","Date", , "Document Type", "Author", "Department", "Effective Date","Status"])
        
        df = pd.DataFrame({
                "Document No": [gs_data.get("Document No", "")] ,
                "Document Version":[gs_data.get("Document Version","")],
                "Name": [gs_data.get( "Name", "")] ,
                "Document Type": [gs_data.get("Document Type", "")] ,
                "Document Subtype": [gs_data.get("Document Subtype", "")] ,
                "Effective Date": [gs_data.get("Effective Date", "")] ,
                "Title": [gs_data.get("Title", "")] 
            })
        #print(df)
        return df

# def extract_spec_images(pdf, output_dir='output_images', min_image_size_kb=12,  min_width=None, min_height=None):
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)

#     # Initialize a list to store data for the DataFrame
#     data = []

#     for page_number, page in enumerate(pdf.pages):
#         print(f"Processing page {page_number + 1}/{len(pdf.pages)}...")

#         images_on_page = []
#         # Iterate through each image on the page
#         for image_index, image in enumerate(page.images):
#             # Extract the coordinates of the image's bounding box
#             image_bbox = (image['x0'], image['top'], image['x1'], image['bottom'])

#             # Crop the page to extract the image
#             cropped_image = page.within_bbox(image_bbox).to_image(resolution=400)

#             # Convert cropped image to PIL image
#             pil_image = cropped_image.original

#             # Check image size
#             image_size_kb = get_image_size(pil_image)
#             if image_size_kb < min_image_size_kb:
#                 print(f"Ignoring image {image_index + 1} on page {page_number + 1} due to size ({image_size_kb:.2f} KB)")
#                 continue

#             # Optionally, you can filter images based on minimum width or height
#             if min_width and pil_image.width < min_width:
#                 print(f"Ignoring image {image_index + 1} on page {page_number + 1} due to width ({pil_image.width}px)")
#                 continue

#             if min_height and pil_image.height < min_height:
#                 print(f"Ignoring image {image_index + 1} on page {page_number + 1} due to height ({pil_image.height}px)")
#                 continue

#             images_on_page.append(pil_image)

#         # If there are multiple images on a page, merge them into a single image
#         if len(images_on_page) > 1:
#             widths, heights = zip(*(i.size for i in images_on_page))

#             total_width = max(widths)
#             total_height = sum(heights)

#             merged_image = Image.new('RGB', (total_width, total_height))

#             y_offset = 0
#             for img in images_on_page:
#                 merged_image.paste(img, (0, y_offset))
#                 y_offset += img.height

#             images_on_page = [merged_image]  # Replace images_on_page with the merged image

#         # Add the images to the list and save them to the output directory
#         for img in images_on_page:
#             image_path = os.path.join(output_dir, f'page_{page_number + 1}image{image_index + 1}.png')
#             img.save(image_path)
#             data.append({'page_number': page_number + 1, 'image_path': image_path, 'image': img})

#     # Create the DataFrame from the list of dictionaries
#     df = pd.DataFrame(data)

#     return df


def extract_spec_images(pdf, output_dir='output_images', min_image_size_kb=20,  min_width=None, min_height=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize a list to store data for the DataFrame
    data = []
    bbox_appended = False
    for page_number, page in enumerate(pdf.pages):
        print(f"Processing page {page_number + 1}/{len(pdf.pages)}...")

        images_on_page = []
        # Iterate through each image on the page
        for image_index, image in enumerate(page.images):

            # Extract the coordinates of the image's bounding box
            filename = pdf.stream.name
            if "SPEC-0012" in filename and not bbox_appended:
                image_bbox = (330, 250, 485, 405)
                bbox_appended = True
                prevent_skip = True
            elif "SPEC-P396" in filename and not bbox_appended:
                image_bbox = (360, 180, 515, 270)
                bbox_appended = True
                prevent_skip = True
            elif "SPEC-P1307" in filename and not bbox_appended:
                image_bbox = (390, 220, 545, 310)
                bbox_appended = True
                prevent_skip = True
            else:
                image_bbox = (image['x0'], image['top'], image['x1'], image['bottom'])
                prevent_skip = False

            # Crop the page to extract the image
            cropped_image = page.within_bbox(image_bbox).to_image(resolution=400)

            # Convert cropped image to PIL image
            pil_image = cropped_image.original

            # Check image size
            image_size_kb = get_image_size(pil_image)
            if not prevent_skip:
              if image_size_kb < min_image_size_kb:
                  print(f"Ignoring image {image_index + 1} on page {page_number + 1} due to size ({image_size_kb:.2f} KB)")
                  continue

              # Optionally, you can filter images based on minimum width or height
              if min_width and pil_image.width < min_width:
                  print(f"Ignoring image {image_index + 1} on page {page_number + 1} due to width ({pil_image.width}px)")
                  continue

              if min_height and pil_image.height < min_height:
                  print(f"Ignoring image {image_index + 1} on page {page_number + 1} due to height ({pil_image.height}px)")
                  continue

            else:
              prevent_skip = False

            images_on_page.append(pil_image)

        # If there are multiple images on a page, merge them into a single image
        if len(images_on_page) > 1:
            widths, heights = zip(*(i.size for i in images_on_page))

            total_width = max(widths)
            total_height = sum(heights)

            merged_image = Image.new('RGB', (total_width, total_height))

            y_offset = 0
            for img in images_on_page:
                merged_image.paste(img, (0, y_offset))
                y_offset += img.height

            images_on_page = [merged_image]  # Replace images_on_page with the merged image

        # Add the images to the list and save them to the output directory
        for img in images_on_page:
            image_path = os.path.join(output_dir, f'page_{page_number + 1}image{image_index + 1}.png')
            img.save(image_path)
            data.append({'page_number': page_number + 1, 'image_path': image_path, 'image': img})

    # Create the DataFrame from the list of dictionaries
    df = pd.DataFrame(data)

    return df



if __name__=="__main__":
    file = "C:\\Users\\admin\\Downloads\\SPEC-P1307 L-Alanine Isopropyl Ester Hydrochloride.pdf"
    pdf = pdfplumber.open(file)
    
    appearance_df = get_first_page_details1(pdf)

    

    
    print(appearance_df)
