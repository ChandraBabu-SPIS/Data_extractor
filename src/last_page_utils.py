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




def get_last_page_data1(pdf):
    last_page = pdf.pages[-1].within_bbox((30,0,pdf.pages[0].width-10, 700))
    if last_page.find_tables():
        table = last_page.extract_table()
        df = pd.DataFrame(table, columns= ["Title", "Document Type", "Author", "Department", "Effective Date","Status"])
        # print("table:", table)
        # print("\n")
        # print(df)
    else:
        # extract all text from page
        gs_data = {}
        texts = last_page.extract_text_simple()
        texts = texts.split("\n")
        


        #print(texts)
        for text in texts:
        
            if "Title:" in text:
                if "Title" not in gs_data.keys():
                    #print("hee")
                    
                # else:
                    gs_data["Title"] = text.split("Title:")[1].strip()
                #print(gs_data)
            elif "Document Type" in text:
                gs_data["Document Type"] = text.split("Document Type:")[1].strip()
            elif "Author:" in text and "Department:" in text:
                author, department = text.split("Department:")
                gs_data["Author"] = author.split("Author:")[1].strip()
                print(department)
                gs_data["Department"] = department.strip()
                
            elif "Effective Date:" in text and "Status:" in text:
                effective_date, status = text.split("Status:")
                gs_data["Effective Date"] = effective_date.split("Effective Date:")[1].strip()
                gs_data["Status"] = status.strip()
        #print(gs_data)
       # ["Approved by","Date", , "Document Type", "Author", "Department", "Effective Date","Status"])
    df = pd.DataFrame({
            "Title": [gs_data.get("Title", "")] ,
            "Document Type": [gs_data.get("Document Type", "")] ,
            "Author": [gs_data.get("Author", "")] ,
            "Department": [gs_data.get("Department", "")] ,
            "Effective Date": [gs_data.get("Effective Date", "")] ,
            "Status": [gs_data.get("Status", "")] 
        })
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
