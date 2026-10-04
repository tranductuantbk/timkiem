import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="AI Smart Search Tool", page_icon="🔍", layout="wide")

st.title("🔍 Công Cụ Tìm Kiếm Thông Minh Tích Hợp AI")
st.markdown("Hệ thống lọc sâu theo vùng miền, nền tảng, ngành nghề để tìm kiếm chính xác nhất.")

# --- BỘ LỌC ĐA CHIỀU NÂNG CAO (UI) ---
st.sidebar.header("🎯 Bộ Lọc Tìm Kiếm Nâng Cao")

# 1. Từ khóa chính
keyword = st.sidebar.text_input("Từ khóa tìm kiếm (*):", placeholder="VD: Xưởng ép nhựa, kho sỉ quần áo...")

# 2. Ngành nghề / Lĩnh vực (Bộ lọc mới)
category = st.sidebar.selectbox("Ngành nghề / Lĩnh vực:", 
                                ["Tất cả", "Sản xuất & Công nghiệp", "Thương mại & Dịch vụ", "F&B (Nhà hàng/Cafe)", "Bất động sản", "Giáo dục", "Khác"])

# 3. Khu vực
locations = ["Toàn quốc", "TP. Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Bình Dương", "Đồng Nai", "Cần Thơ"]
location = st.sidebar.selectbox("Khu vực / Vùng miền:", locations)

# 4. Nền tảng tìm kiếm (Đã khôi phục và làm rõ)
st.sidebar.markdown("**Nền tảng quét dữ liệu:**")
plat_fb = st.sidebar.checkbox("Facebook (Fanpage/Group)", value=True)
plat_tt = st.sidebar.checkbox("TikTok (Video/Shop)")
plat_web = st.sidebar.checkbox("Trang Mạng (Website/Google Search)", value=True)
plat_map = st.sidebar.checkbox("Google Maps (Địa điểm doanh nghiệp)", value=True)

# 5. Yêu cầu bắt buộc (Bộ lọc mới để tăng độ chính xác)
st.sidebar.markdown("**Yêu cầu bắt buộc (Lọc nhiễu):**")
require_phone = st.sidebar.checkbox("Bắt buộc phải có Số điện thoại", value=True)
require_address = st.sidebar.checkbox("Bắt buộc phải có Địa chỉ rõ ràng", value=True)

api_key = st.sidebar.text_input("Nhập API Key (Gemini/OpenAI):", type="password", help="Kích hoạt AI để xử lý dữ liệu")

# --- LOGIC TẠO PDF ---
def export_pdf(df, keyword, location):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    
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
        
    result = pdf.output(dest='S')
    if isinstance(result, str):
        return result.encode('latin-1')
    else:
        return bytes(result)

# --- LOGIC AI BÓC TÁCH & TÌM KIẾM ---
def run_ai_search(kw, loc, cat, req_phone, req_address):
    # Dữ liệu mô phỏng (trong thực tế, AI sẽ dựa vào req_phone và req_address để lọc JSON)
    mock_data = [
        {
            "Tên Cơ Sở": f"Công ty TNHH {kw} Việt Nam ({cat})",
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
        with st.spinner("⏳ Đang quét dữ liệu và áp dụng bộ lọc nâng cao..."):
            df_results = run_ai_search(keyword, location, category, require_phone, require_address)
            
            st.success(f"✅ Đã phân tích xong! Tìm thấy {len(df_results)} kết quả phù hợp tiêu chí.")
            st.dataframe(df_results, use_container_width=True)
            
            pdf_bytes = export_pdf(df_results, keyword, location)
            st.download_button(
                label="📄 Tải Xuống Báo Cáo (PDF)",
                data=pdf_bytes,
                file_name=f"KetQuaTimKiem_{keyword.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
