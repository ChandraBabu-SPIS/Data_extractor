import io
import os
import subprocess
from subprocess import STDOUT, check_call

import pandas as pd
import streamlit as st

### Custom utils
from src.main import extract_from_document
from pdfminer.pdfparser import PSSyntaxError


# @st.cache_data
# def gh():
#     proc = subprocess.Popen('apt-get install -y ghostscript', shell=True, stdin=None, stdout=open(os.devnull,'wb'), stderr=STDOUT, executable="/bin/bash")

# gh()

st.title('Soulpage IT')
st.subheader("Data Extraction Demo")


uploaded_file = st.file_uploader("Choose a file", type="pdf")
if uploaded_file is not None:
    st.write("File uploaded")
          
    if uploaded_file.name.startswith("SPEC"):
        st.write("File process STARTED")
        file_name = uploaded_file.name
        output_file = os.path.splitext(file_name)[0]+".xlsx"
        output_img_file = os.path.splitext(file_name)[0]+".png"
        
        try:
            # see if it is a DIGITAL Document
            result_df = extract_from_document(uploaded_file)
            if result_df is not None:
                result_df.to_excel(output_file)
                # structure_img.save(output_img_file)

            st.write("File processing COMPLETED")

            #### TO DOWNLOAD FILE
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    # Write each dataframe to a different worksheet.
                    result_df.to_excel(writer, sheet_name='Sheet1', index=False)

            st.download_button(
                    label="Download CSV",
                    data=buffer.getvalue(),
                    file_name = f"{output_file}",
                    mime="application/vnd.ms-excel",
                    key='download-csv'
                    )
            
            # img_buffer = io.BytesIO()
            # structure_img.save(img_buffer, format="PNG")
            # img_buffer.seek(0)

            # st.download_button(
            #         label="Download Image",
            #         data=img_buffer,
            #         file_name = f"{output_img_file}",
            #         mime="image/png",
            #         key='download-image'
            #         )

        except PSSyntaxError as e:
            st.write(f"PSSyntaxError occurred while processing file {uploaded_file.name}: {e}")
        except Exception as e:
            st.write(f"An error occurred while processing file {uploaded_file.name}: {e}")     

    else:
          st.write("Couldn't Process the File. Upload proper File..")
