import os
import pdfplumber
import pandas as pd

def crop_borders(page, pdf):
    return page.within_bbox((30,30,pdf.pages[0].width-30, 700))


def crop_pdf(page):
  
    width = page.width
    height = page.height
    
    x0_ver = width / 21
    x1_ver = width - (width / 20)
    y0_ver = 0
    y1_ver = height
    vertically_cropped_pdf = page.crop((x0_ver, y0_ver, x1_ver, y1_ver))

    return vertically_cropped_pdf, x0_ver


def find_revision_history_from_and_to_pages(pdf):
    for pg_indx, page in enumerate(pdf.pages):
        cropped_page, _ = crop_pdf(page)
        pg_text = cropped_page.extract_text()

        # Place holder
        revision_history_page = 0
        if "HISTORY OF REVISIONS" in pg_text or "REVISION HISTORY" in pg_text and revision_history_page==0:
            revision_history_page = pg_indx
            break
        
        # Place holder
        approved_by_page = -1 # except last page
        if "Approved by" in pdf.pages[-1].extract_text():
            approved_by_page = len(pdf.pages)-1
    return revision_history_page, approved_by_page



def find_horizontal_cords(page):
    horizontal_line_bottom_cord = max([edge["bottom"] for edge in page.horizontal_edges])
    page_bottom_cord = max([ln["bottom"] for ln in page.extract_text_lines(return_chars=False)])
    return horizontal_line_bottom_cord, page_bottom_cord


def find_vertical_cords(page):
    vertical_line_right_border_cord = max([edge["bottom"] for edge in page.chars])
    return vertical_line_right_border_cord

def get_table_settings(page):
    horizontal_line_bottom_cord, page_bottom_cord = find_horizontal_cords(page)
    vertical_line_right_border_cord = find_vertical_cords(page)

    table_settings = {"vertical_strategy": "text", 
                        "horizontal_strategy": "lines_strict",
                        "explicit_horizontal_lines":[horizontal_line_bottom_cord, page_bottom_cord],
                        # "explicit_horizontal_lines":page.edges+page.curves,
                        "explicit_vertical_lines": [70,120, vertical_line_right_border_cord],
                        "join_y_tolerance":3, # nouse
                        "join_x_tolerance":3, # nouse
                        "snap_y_tolerance":50, # nouse
                        "edge_min_length":44, # nouse
                        "intersection_y_tolerance":55
                        }
    return table_settings


def extract_revision_history(pdf):
    start_page, end_page = find_revision_history_from_and_to_pages(pdf)
    # print("START and END pages:", start_page, end_page)
    total_revision_history_dfs = []
    total_revision_history_text = []
    for page in pdf.pages[start_page:end_page]:
        page = crop_borders(page, pdf)

        ############# Giving layout extraction for now ################
        #### as below method, CSV columns are not properly aligned ####
        text = page.extract_text(layout=True)
        total_revision_history_text.append(text)

        ########### CSV Extraction Method ##########
        table_settings = get_table_settings(page)
        table = page.extract_table(table_settings)
        if table:
            table = table[0] #lets say that it only gets a Single complete table
            columns = [f"Revision_history_{col_indx}" for col_indx,_  in enumerate(table)]
            df = pd.DataFrame([table], columns= columns)
            total_revision_history_dfs.append(df)
        else:
            total_revision_history_dfs.append(pd.DataFrame())    
    # combined_df = pd.concat(total_revision_history_dfs, ignore_index=True, sort=False, axis=0)
    # return combined_df
    total_revision_history_text = "\n".join(total_revision_history_text)
    return total_revision_history_text

if __name__ == "__main__":    
    file = "D:\Purna_Office\Soulpage_New\Task-50_0_GILEAD\Extended_POC_2\SPEC-0012 Elvitegravir Drug Substance.pdf"
    pdf = pdfplumber.open(file)

    final_layout_text = extract_revision_history(pdf)
    final_df = extract_revision_history(pdf)

    final_layout_text_df = pd.DataFrame([final_layout_text], columns=["Revision History"])
    final_layout_text_df.to_csv("revision_hisory.csv")
    
