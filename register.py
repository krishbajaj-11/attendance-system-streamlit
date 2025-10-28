import streamlit as st
import boto3
import json

# Initialize AWS clients
rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

# AWS Resources
COLLECTION_ID = "attendance-collection"
BUCKET_NAME = "attendance-student-photos-krish"

st.title("🧑‍🎓 Face Registration Portal")
st.write("Register a student face into AWS Rekognition Collection")

# --- Upload Section ---
student_name = st.text_input("Enter Student Name")
uploaded_file = st.file_uploader("Upload a clear face image", type=["jpg", "jpeg", "png"])

if uploaded_file and student_name:
    if st.button("Register Face"):
        # Upload image to S3
        s3.upload_fileobj(uploaded_file, BUCKET_NAME, uploaded_file.name)
        st.success(f"✅ Uploaded {uploaded_file.name} to S3")

        # Add face to Rekognition collection
        response = rekognition.index_faces(
            CollectionId=COLLECTION_ID,
            Image={"S3Object": {"Bucket": BUCKET_NAME, "Name": uploaded_file.name}},
            ExternalImageId=student_name,
            DetectionAttributes=["DEFAULT"]
        )

        st.json(response)
        st.success(f"🎉 Face registered for student: {student_name}")
