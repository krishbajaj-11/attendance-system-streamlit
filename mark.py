import boto3
import streamlit as st
from datetime import datetime

# Existing clients
rekognition = boto3.client('rekognition', region_name='ap-south-1')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('AttendanceTable')

bucket_name = 'attendance-student-photos-krish'
collection_id = 'attendance-collection'

st.header("📸 Mark Attendance")

test_image = st.file_uploader("Upload image to mark attendance", type=["jpg", "jpeg", "png"], key="attendance")

if test_image:
    with open(test_image.name, "wb") as f:
        f.write(test_image.getbuffer())

    # Upload image to S3
    s3.upload_file(test_image.name, bucket_name, test_image.name)
    st.info("Image uploaded to S3 successfully ✅")

    # Search the face in the Rekognition collection
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
        
        # Mark attendance in DynamoDB
        timestamp = datetime.utcnow().isoformat()
        table.put_item(Item={
            'StudentName': student_name,
            'Timestamp': timestamp
        })
        
        st.success(f"✅ Attendance marked for {student_name} ({similarity:.2f}% match)")
        st.write("🕒 Time:", timestamp)

    else:
        st.error("❌ No matching face found. Try another photo.")
