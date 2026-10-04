import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF
import json

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="AI Smart Search Tool", page_icon="🔍", layout="wide")

st.title("🔍 Công Cụ Tìm Kiếm Thông Minh Tích Hợp AI")
st.markdown("Hệ thống lọc sâu theo vùng miền, nền tảng và tự động bóc tách số điện thoại, địa chỉ bằng Trí tuệ nhân tạo.")

# --- BỘ LỌC ĐA CHIỀU (UI) ---
st.sidebar.header("🎯 Bộ Lọc Tìm Kiếm")
keyword = st.sidebar.text_input("Từ khóa tìm kiếm:", placeholder="VD: Xưởng ép nhựa, thiết bị tự động hóa...")

locations = ["Toàn quốc", "TP. Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Bình Dương", "Đồng Nai", "Cần Thơ"]
location = st.sidebar.selectbox("Khu vực / Vùng miền:", locations)

st.sidebar.markdown("**Nền tảng tìm kiếm:**")
plat_fb = st.sidebar.checkbox("Facebook", value=True)
plat_tt = st.sidebar.checkbox("TikTok")
plat_web = st.sidebar.checkbox("Trang Mạng (Website/Google)", value=True)

api_key = st.sidebar.text_input("Nhập API Key (Gemini/OpenAI):", type="password", help="Kích hoạt AI để xử lý dữ liệu")

# --- LOGIC TẠO PDF ---
def export_pdf(df, keyword, location):
    pdf = FPDF()
    pdf.add_page()
    
    # Lưu ý: Trong môi trường thực tế, cần add_font Unicode (VD: Arial Unicode MS) để hiển thị dấu Tiếng Việt hoàn chỉnh
    # Dưới đây dùng font Arial mặc định (có thể không hiển thị đủ dấu trong môi trường cơ bản)
    pdf.set_font("Arial", size=14)
    
    # Chuyển đổi tên để in ra PDF không bị lỗi font cơ bản
    safe_keyword = str(keyword).encode('latin-1', 'replace').decode('latin-1')
    safe_location = str(location).encode('latin-1', 'replace').decode('latin-1')
    
    pdf.cell(200, 10, txt=f"BAO CAO TIM KIEM: {safe_keyword}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Khu vuc: {safe_location} | Ngay xuat: {datetime.datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
    pdf.ln(10)
    
    for index, row in df.iterrows():
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(200, 8, txt=f"Ten co so: {str(row['Tên Cơ Sở']).encode('latin-1', 'replace').decode('latin-1')}", ln=True)
        
        pdf.set_font("Arial", '', 10)
        pdf.cell(200, 8, txt=f"Dia chi: {str(row['Địa Chỉ']).encode('latin-1', 'replace').decode('latin-1')}", ln=True)
        pdf.cell(200, 8, txt=f"SDT: {str(row['Số Điện Thoại'])}", ln=True)
        pdf.cell(200, 8, txt=f"Nen tang: {str(row['Nền Tảng']).encode('latin-1', 'replace').decode('latin-1')}", ln=True)
        pdf.multi_cell(0, 8, txt=f"Chi tiet: {str(row['Chi Tiết']).encode('latin-1', 'replace').decode('latin-1')}")
        pdf.ln(5)
        
    # Xuất file dạng bytes để Streamlit tải xuống
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIC AI BÓC TÁCH & TÌM KIẾM ---
def run_ai_search(kw, loc, fb, tt, web):
    # Prompt logic đưa cho AI (Mô phỏng)
    ai_prompt = f"""
    Bạn là chuyên gia khai thác dữ liệu. Hãy đọc nội dung thô từ internet và bóc tách thông tin liên quan đến '{kw}' 
    chỉ tại khu vực '{loc}'.
    Yêu cầu trả về JSON chuẩn xác với các field:
    - Tên Cơ Sở
    - Địa Chỉ (Nếu không thuộc {loc}, hãy loại bỏ kết quả này)
    - Số Điện Thoại (Bắt buộc phải tìm chuỗi 10 số)
    - Nền Tảng
    - Chi Tiết
    """
    
    # ĐÂY LÀ DỮ LIỆU MÔ PHỎNG (Mock Data) kết quả sau khi AI xử lý JSON
    # Trong ứng dụng thực, bạn sẽ gọi genai.generate_text() hoặc openai.ChatCompletion.create() tại đây
    mock_data = [
        {
            "Tên Cơ Sở": f"Công ty TNHH {kw} Việt Nam",
            "Địa Chỉ": f"Khu công nghiệp A, {loc if loc != 'Toàn quốc' else 'TP. Hồ Chí Minh'}",
            "Số Điện Thoại": "0901234567",
            "Nền Tảng": "Website",
            "Chi Tiết": f"Chuyên phân phối {kw} chính hãng, hỗ trợ kỹ thuật 24/7."
        },
        {
            "Tên Cơ Sở": f"Cửa hàng {kw} Minh Phát",
            "Địa Chỉ": f"Số 123 Đường Nguyễn Văn A, {loc if loc != 'Toàn quốc' else 'TP. Hồ Chí Minh'}",
            "Số Điện Thoại": "0987654321",
            "Nền Tảng": "Facebook",
            "Chi Tiết": f"Bán buôn, bán lẻ {kw}. Giao hàng tận nơi."
        }
    ]
    return pd.DataFrame(mock_data)

# --- NÚT BẤM VÀ HIỂN THỊ KẾT QUẢ ---
if st.sidebar.button("🚀 Bắt Đầu Tìm Kiếm", type="primary"):
    if not keyword:
        st.warning("⚠️ Vui lòng nhập từ khóa tìm kiếm!")
    else:
        with st.spinner("⏳ Đang quét dữ liệu và sử dụng AI bóc tách thông tin..."):
            
            # Gọi hàm xử lý cốt lõi
            df_results = run_ai_search(keyword, location, plat_fb, plat_tt, plat_web)
            
            st.success(f"✅ Đã phân tích xong! Tìm thấy {len(df_results)} kết quả phù hợp tại {location}.")
            
            # 1. Hiển thị bảng dữ liệu (Dataframe) cho người dùng xem và lọc thêm
            st.dataframe(df_results, use_container_width=True)
            
            # 2. Xử lý xuất file PDF
            pdf_bytes = export_pdf(df_results, keyword, location)
            
            st.download_button(
                label="📄 Tải Xuống Báo Cáo (PDF)",
                data=pdf_bytes,
                file_name=f"KetQuaTimKiem_{keyword.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

