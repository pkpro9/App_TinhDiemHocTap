import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Kết nối Google Sheet
GSPREAD_URL = "https://docs.google.com/spreadsheets/d/1Vj1xMKS521etE3eL-rexbBXPucKGAiYpsQnpSIJPJeA/edit?gid=0"

def connect_to_google_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(GSPREAD_URL)
    return sheet

# Tính điểm trung bình
def calculate_average(data):
    result = []
    for semester in data["semester"].unique():
        semester_data = data[data["semester"] == semester]
        for subject in semester_data["subject"].unique():
            subject_data = semester_data[semester_data["subject"] == subject]
            weighted_sum = sum(subject_data["score"] * subject_data["weight"])
            total_weights = sum(subject_data["weight"])
            avg = round(weighted_sum / total_weights, 2) if total_weights > 0 else 0
            result.append({"Học kỳ": semester, "Môn học": subject, "Điểm trung bình": avg})
    return pd.DataFrame(result)

# App Streamlit
st.title("App tính điểm học tập")

# Kết nối Google Sheet
sheet = connect_to_google_sheet()

# Lấy dữ liệu danh sách môn học từ sheet1
def get_subjects_from_sheet(sheet):
    sheet1 = sheet.get_worksheet(0)  # Lấy sheet1
    subjects = sheet1.col_values(1)  # Lấy dữ liệu cột "subject"
    subjects = [sub.strip() for sub in subjects if sub.strip()]  # Loại bỏ giá trị trống và khoảng trắng
    return subjects

subjects = get_subjects_from_sheet(sheet)
test_types = ["Kiểm tra thường xuyên", "Giữa kỳ", "Cuối Kỳ", "Thi học kỳ"]
semesters = ["Học kỳ I", "Học kỳ II"]

# Kiểm tra và khởi tạo session_state
if "subject" not in st.session_state:
    st.session_state["subject"] = subjects[0] if subjects else ""
if "test_type" not in st.session_state:
    st.session_state["test_type"] = "Kiểm tra thường xuyên"
if "score" not in st.session_state:
    st.session_state["score"] = 0.0
if "semester" not in st.session_state:
    st.session_state["semester"] = semesters[0]

# Giao diện người dùng
subject = st.selectbox("Môn học", options=subjects, key="subject")
test_type = st.selectbox("Chọn loại kiểm tra", options=test_types, key="test_type")
semester = st.selectbox("Học kỳ", options=semesters, key="semester")
score = st.number_input("Nhập số điểm", min_value=0.0, max_value=10.0, step=0.1, key="score")

# Hệ số dựa trên loại kiểm tra
weights = {
    "Kiểm tra thường xuyên": 1,
    "Giữa kỳ": 1,
    "Cuối Kỳ": 2,
    "Thi học kỳ": 3,
}

# Nút "Ghi nhận"
if st.button("Ghi nhận"):
    weight = weights[test_type]
    try:
        # Ghi dữ liệu vào sheet2
        sheet2 = sheet.get_worksheet(1)  # Lấy sheet2
        sheet2.append_row([semester, subject, test_type, st.session_state["score"], weight])
        st.success(f"Đã ghi nhận thông tin vào Google Sheet!")
    except Exception as e:
        st.error(f"Lỗi khi ghi nhận thông tin: {e}")

# Nút "Tính điểm trung bình"
if st.button("Tính điểm trung bình"):
    try:
        # Lấy tất cả dữ liệu từ sheet2
        sheet2 = sheet.get_worksheet(1)
        records = sheet2.get_all_records()
        if records:
            data = pd.DataFrame(records)
            required_columns = {"semester", "subject", "test_type", "score", "weight"}
            if not required_columns.issubset(data.columns):
                st.error("Dữ liệu trong Google Sheet thiếu các cột cần thiết: 'semester', 'subject', 'test_type', 'score', 'weight'")
            else:
                # Tính điểm trung bình và hiển thị bảng
                data["weight"] = data["weight"].astype(float)
                data["score"] = data["score"].astype(float)
                average_df = calculate_average(data)
                st.subheader("Bảng điểm trung bình theo môn học và học kỳ")
                st.dataframe(average_df)
        else:
            st.warning("Chưa có dữ liệu trong Google Sheet!")
    except Exception as e:
        st.error(f"Lỗi khi tính điểm trung bình: {e}")
