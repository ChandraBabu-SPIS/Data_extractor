import pandas as pd
import pdfplumber

def get_footer_dict(lines):
    footer_dict= {}
    # last 3 lines
    for line in lines[-3:]:
        if line.startswith("Doc"):
            words = line.split(" ")
            words.insert(3,".")
            words.insert(4,".")
            words.insert(5,".")
            line = " ".join(words)
            
        words = line.split(" ")
        
        key = " ".join(words[:2])
        value = " ".join([word for word in words[2:5] if len(word)>1])
        footer_dict[key] = value

        key1 = " ".join(words[5:8])
        value1 = " ".join(words[8:])
        footer_dict[key1] = value1
    return footer_dict



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


if __name__=="__main__":
    file = "D:\Purna_Office\Soulpage_New\Task-50_0_GILEAD\Extended_POC_2\SPEC-0012 Elvitegravir Drug Substance.pdf"
    pdf = pdfplumber.open(file)

    footer = pdf.pages[0].crop((0, 700, pdf.pages[0].width, pdf.pages[0].height))
    footerlines = footer.extract_text_simple().split("\n")
    footer_data = get_footer_dict(footerlines)
    footer_df = pd.DataFrame([footer_data])
    print("footer df:", footer_df)


    df  = get_last_page_data(pdf)
    print("last page df:", df)