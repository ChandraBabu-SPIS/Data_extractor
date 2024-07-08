import pdfplumber
import pandas as pd
import numpy as np

from PIL import Image
from decimer_segmentation import segment_chemical_structures
from IPython.display import HTML
import os

def get_first_page_details1(pdf):
    text = pdf.pages[0].extract_text(x_tolerance=5, y_tolerance=5)
    sample_dict = {}

    for row in text.split("\n"):
        if "VERSION" in row:
            document_details, sample_dict["VERSION"] = row.split("VERSION:")
            sample_dict["VERSION"] = sample_dict["VERSION"].strip().split(" ")[0]
            if "DOCUMENT NO" in document_details:
                sample_dict["DOCUMENT NO.:"] = document_details.split("DOCUMENT NO.:")[1]

        elif ":" in row:
            print("Row", row)
            key, val = row.split(":")
            if len(key)>1 and len(val)>1:
                sample_dict[key] = val
    return sample_dict


def get_appearance_block(table):
    new_table = []
    for row in table:
        val1, val2 = row
        if len(val1) != 0:
            new_table.append(row)
    df = pd.DataFrame(new_table[1:], columns=["SPECIFICATION","METHOD"])
    return df

def find_appearance_block1(pdf):
    line_identifier1 = "METHOD"

    specification_df = pd.DataFrame()
    for page in pdf.pages[:-2]:
        page = page.crop((30,0, page.width-25, page.height))
        text = page.extract_text()

        if line_identifier1 in text:
            rows = text.split("\n")
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
            # print(table)
            df = get_appearance_block(table)
            specification_df = pd.concat([specification_df, df], axis=0)
            specification_df = specification_df.reset_index(drop=True)

    return specification_df


def get_revision_history1(pdf):
    revision_hisory_df = pd.DataFrame()
    for page in pdf.pages:
        pg_text = page.extract_text()
        if "HISTORY OF REVISIONs" in pg_text or "REVISION HISTORY" in pg_text or "VERSION HISTORY" in pg_text:
            # print(page)
            # print(pg_text)
            table = page.extract_table()
            # print(table)
            # removing NONE vlaues and cleaning table
            new_table = []
            for row in table:
                new_row = [val for val in row if val is not None]
                if len(new_row)>2:
                    print(new_row)
                    new_table.append(new_row)

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
    segments = segment_chemical_structures(page1, expand= True)
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

def get_last_page_data(pdf):
    last_page = pdf.pages[-1].within_bbox((30,0,pdf.pages[0].width-10, 700))
    if last_page.find_tables():
        table = last_page.extract_table()
        df = pd.DataFrame(table, columns= ["Approved by","Date"])
        # print("table:", table)
        # print("\n")
        # print(df)
    else:
        # extract all text from page
        texts = last_page.extract_text_simple()
        texts = texts.split("\n")
        approvals = []
        dates = []
        for text in texts:
            if "date" and "approv" in text.lower():
                if "Date" in text:
                    # print(text.split("Date"))
                    col1, col2 = text.split("Date")
                    approvals.append(col1)
                    dates.append(col2)
            else:
                pass
                # print(text)
        df = pd.DataFrame({"Approved by":approvals, "Date":dates})
        # print(df)
    return df

def extract_spec_images(pdf, output_dir='output_images'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize a list to store data for the DataFrame
    data = []

    for page_number, page in enumerate(pdf.pages):
        print(f"Processing page {page_number + 1}/{len(pdf.pages)}...")

        images_on_page = []
        # Iterate through each image on the page
        for image_index, image in enumerate(page.images):
            # Extract the coordinates of the image's bounding box
            image_bbox = (image['x0'], image['top'], image['x1'], image['bottom'])

            # Crop the page to extract the image
            cropped_image = page.within_bbox(image_bbox).to_image(resolution=400)

            # Convert cropped image to PIL image
            pil_image = cropped_image.original
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
            image_path = os.path.join(output_dir, f'page_{page_number + 1}_image_{image_index + 1}.png')
            img.save(image_path)
            data.append({'page_number': page_number + 1, 'image_path': image_path, 'image': img})

    # Create the DataFrame from the list of dictionaries
    df = pd.DataFrame(data)
    
    return df



