import pandas as pd
import pdfplumber
import re

def crop_borders(page, pdf):
    return page.within_bbox((30,30,pdf.pages[0].width-30, 700))

def get_appearance_block(table):
    # new_table = []
    # for row in table:
    #     # print("row", row)
    #     try:
    #         val1, val2 = row
    #         if len(val1) != 0 or len(val2) != 0:
    #             new_table.append(row)
    #     except:
    #         continue

    df = pd.DataFrame(table[1:], columns=["SPECIFICATION","METHOD"])
    return df

def find_appearance_block(pdf):
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

def extract_description(page):
    layout_text = page.extract_text(layout = True)
    layout_text_list = [line for line in layout_text.split("\n") if line.strip()]
    
    line_no = [line_no for line_no, line in enumerate(layout_text_list) if "DESCRIPTION" in line][0]
    description_text = "\n".join(layout_text_list[line_no+1:])
    return description_text

if __name__=="__main__":
    file = "D:\Purna_Office\Soulpage_New\Task-50_0_GILEAD\Extended_POC_2\SPEC-0012 Elvitegravir Drug Substance.pdf"
    pdf = pdfplumber.open(file)
    
    appearance_df = find_appearance_block(pdf)
    
    for page in pdf.pages:
        page  = crop_borders(page, pdf)
        text = page.extract_text()
        if "DESCRIPTION" in text:
            description_text = extract_description(page)
    description_df = pd.DataFrame([description_text], columns=["Description"])

    print(description_df)
    print(appearance_df)