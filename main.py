import streamlit as st
import boto3
from datetime import datetime, UTC
import pandas as pd

# ============================
# AWS Configuration
# ============================
region = 'ap-south-1'
bucket_name = 'attendance-student-photos-arpan'
collection_id = 'attendance-collection'
table_name = 'AttendanceLogs'  # New table (StudentName + Timestamp as keys)

rekognition = boto3.client('rekognition', region_name=region)
s3 = boto3.client('s3', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)
table = dynamodb.Table(table_name)

# ============================
# Streamlit Page Config
# ============================
st.set_page_config(page_title="AWS Attendance System", page_icon="📸", layout="centered")
st.title("📸 Smart Attendance System using AWS Rekognition")
st.sidebar.title("🧭 Navigation")

menu = st.sidebar.radio("Select a feature", ["Register Face", "Mark Attendance", "View Attendance Logs"])

# ============================
# 1️⃣ Register Face
# ============================
if menu == "Register Face":
    st.header("🧑‍💼 Register New Face")
    name = st.text_input("Enter student name (no spaces):").strip()

    uploaded_file = st.file_uploader("Upload student's face image", type=["jpg", "jpeg", "png"])

    if uploaded_file and name:
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Check if name already exists in collection
        existing_faces = rekognition.list_faces(CollectionId=collection_id, MaxResults=1000)
        already_registered = any(face['ExternalImageId'] == name for face in existing_faces['Faces'])

        if already_registered:
            st.warning(f"⚠️ Face for '{name}' is already registered. Skipping re-registration.")
        else:
            # Upload to S3
            s3.upload_file(uploaded_file.name, bucket_name, uploaded_file.name)
            st.info("✅ Uploaded to S3")

            # Index face in Rekognition
            response = rekognition.index_faces(
                CollectionId=collection_id,
                Image={'S3Object': {'Bucket': bucket_name, 'Name': uploaded_file.name}},
                ExternalImageId=name,
                DetectionAttributes=['DEFAULT']
            )
            st.success(f"✅ Face registered for: {name}")
            st.json(response)

# ============================
# 2️⃣ Mark Attendance
# ============================
elif menu == "Mark Attendance":
    st.header("📸 Mark Attendance")
    test_image = st.file_uploader("Upload image to mark attendance", type=["jpg", "jpeg", "png"])

    if test_image:
        with open(test_image.name, "wb") as f:
            f.write(test_image.getbuffer())

        # Upload to S3
        s3.upload_file(test_image.name, bucket_name, test_image.name)
        st.info("✅ Image uploaded to S3")

        # Search for matching face
        response = rekognition.search_faces_by_image(
            CollectionId=collection_id,
            Image={'S3Object': {'Bucket': bucket_name, 'Name': test_image.name}},
            FaceMatchThreshold=90,
            MaxFaces=1
        )

        if response['FaceMatches']:
            match = response['FaceMatches'][0]
            student_name = match['Face']['ExternalImageId']
            similarity = match['Similarity']
            
            # ✅ Use timezone-aware UTC timestamp
            timestamp = datetime.now(UTC).isoformat()

            # ✅ Add new record each time (don’t overwrite)
            table.put_item(Item={
                'StudentName': student_name,
                'Timestamp': timestamp
            })

            st.success(f"✅ Attendance marked for {student_name}")
            st.write(f"🕒 Time: {timestamp}")
            st.write(f"🎯 Match confidence: {similarity:.2f}%")
        else:
            st.error("❌ No matching face found. Try again with a clearer image.")

# ============================
# 3️⃣ View Attendance Logs
# ============================
elif menu == "View Attendance Logs":
    st.header("📋 Attendance Logs")

    try:
        response = table.scan()
        items = response.get('Items', [])

        if not items:
            st.warning("No attendance records found yet.")
        else:
            df = pd.DataFrame(items)
            df = df.sort_values(by="Timestamp", ascending=False)

            st.dataframe(df, use_container_width=True)

            # Option to download CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Download as CSV",
                data=csv,
                file_name="attendance_logs.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error fetching logs: {e}")
