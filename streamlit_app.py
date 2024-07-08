import io
import os
import pandas as pd
import streamlit as st
import pdfplumber
from src.main import extract_from_document,extract_spec_p_info
from src.SPEC_P_utils import extract_spec_images
from pdfminer.pdfparser import PSSyntaxError
import zipfile

st.title('Soulpage IT')
st.subheader("Data Extraction Demo")

# Section for general PDF processing
#


doc_type = st.radio(
    "CHOOSE DOCUMENT TYPE: ",
    [ "Quality Specification","Raw Material"],
    index=None,
)


if doc_type =="Quality Specification":
    st.header("Quality Specification PDF")
    uploaded_file = st.file_uploader("Choose a file", type="pdf", key="Quality Specification")
    if uploaded_file is not None:
        st.write("File uploaded")
        
        if uploaded_file.name.startswith("SPEC"):
            st.write("File process STARTED")
            file_name = uploaded_file.name
            output_file = os.path.splitext(file_name)[0] + ".xlsx"
            
            
            try:
                # Attempt to extract data from the document
                result_df = extract_from_document(uploaded_file)
                if result_df is not None:
                    result_df.to_excel(output_file)
                    
                st.write("File processing COMPLETED")

                # Prepare the file for download
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    result_df.to_excel(writer, sheet_name='Sheet1', index=False)

                st.download_button(
                    label="Download Excel",
                    data=buffer.getvalue(),
                    file_name=output_file,
                    mime="application/vnd.ms-excel",
                    key='download-excel'
                )

            except PSSyntaxError as e:
                st.write(f"PSSyntaxError occurred while processing file {uploaded_file.name}: {e}")
            except Exception as e:
                st.write(f"An error occurred while processing file {uploaded_file.name}: {e}")     
        else:
            st.write("Couldn't Process the File. Upload proper File.")
            
    # Section for SPEC P PDF processing


elif doc_type =="Raw Material":

    st.header("Raw Material PDF")
    uploaded_spec_p_file = st.file_uploader("Choose a SPEC P file", type="pdf", key="spec_p_pdf")
    if uploaded_spec_p_file is not None:
        st.write("SPEC P File uploaded")
        
        file_name = uploaded_spec_p_file.name
        output_file = os.path.splitext(file_name)[0] + "_spec_p.xlsx"
        
        try:
            # Attempt to extract data from the SPEC P document
            spec_p_result_df = extract_spec_p_info(uploaded_spec_p_file)
            if spec_p_result_df is not None:
                spec_p_result_df.to_excel(output_file)
                
            st.write("SPEC P File processing COMPLETED")

            # Prepare the SPEC P file for download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                spec_p_result_df.to_excel(writer, sheet_name='Sheet1', index=False)

            st.download_button(
                label="Download SPEC P Excel",
                data=buffer.getvalue(),
                file_name=output_file,
                mime="application/vnd.ms-excel",
                key='download-spec-p-excel'
            )

            # Extract images from the SPEC P PDF
            with pdfplumber.open(uploaded_spec_p_file) as pdf:
                img_df = extract_spec_images(pdf)
            
            # Create a zip file for all images
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zf:
                for idx, row in img_df.iterrows():
                    img_buffer = io.BytesIO()
                    row['image'].save(img_buffer, format="PNG")
                    img_buffer.seek(0)
                    zf.writestr(f"page_{row['page_number']}_image_{idx + 1}.png", img_buffer.getvalue())
            
            zip_buffer.seek(0)
            
            st.download_button(
                label="Download All Images",
                data=zip_buffer,
                file_name="extracted_images.zip",
                mime="application/zip",
                key='download-all-images'
            )

        except PSSyntaxError as e:
            st.write(f"PSSyntaxError occurred while processing file {uploaded_spec_p_file.name}: {e}")
        except Exception as e:
            st.write(f"An error occurred while processing file {uploaded_spec_p_file.name}: {e}")
