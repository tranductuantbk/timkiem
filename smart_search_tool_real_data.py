import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF
import json
import re

# Thư viện tìm kiếm thực tế và AI
try:
    from duckduckgo_search import DDGS
    import google.generativeai as genai
except ImportError:
    st.error("⚠️ Bạn cần cài đặt thêm thư viện: pip install duckduckgo-search google-generativeai")

st.set_page_config(page_title="AI Smart Search Tool - Real Data", page_icon="🔍", layout="wide")

st.title("🔍 Công Cụ Tìm Kiếm Tích Hợp AI (Dữ Liệu Thực)")
st.markdown("Hệ thống quét dữ liệu trực tiếp từ Internet, kết hợp bộ lọc thời gian, mức giá và AI để bóc tách thông tin.")

# --- BỘ LỌC ĐA CHIỀU (UI) ---
st.sidebar.header("🎯 Bộ Lọc Tìm Kiếm Nâng Cao")

keyword = st.sidebar.text_input("Từ khóa tìm kiếm (*):", placeholder="VD: Xưởng ép nhựa, kho sỉ quần áo...")
category = st.sidebar.selectbox("Ngành nghề / Lĩnh vực:", 
                                ["Tất cả", "Sản xuất & Công nghiệp", "Thương mại & Dịch vụ", "F&B", "Bất động sản", "Khác"])
locations = ["Toàn quốc", "TP. Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Bình Dương", "Đồng Nai", "Cần Thơ"]
location = st.sidebar.selectbox("Khu vực / Vùng miền:", locations)

# 1. Thêm bộ lọc thời gian
time_options = ["Tất cả", "1 tháng", "3 tháng", "6 tháng", "9 tháng", "1 năm"]
time_filter = st.sidebar.selectbox("Thời gian đăng thông tin:", time_options)

# 2. Thêm bộ lọc sắp xếp giá
price_sort = st.sidebar.radio("Sắp xếp theo mức giá:", ["Không sắp xếp", "Từ thấp đến cao", "Từ cao đến thấp"])

st.sidebar.markdown("**Yêu cầu bắt buộc (Lọc nhiễu):**")
require_phone = st.sidebar.checkbox("Bắt buộc phải có Số điện thoại", value=True)
require_address = st.sidebar.checkbox("Bắt buộc phải có Địa chỉ rõ ràng", value=True)

# Lựa chọn số lượng kết quả muốn quét
num_search = st.sidebar.slider("Số lượng trang web muốn quét:", min_value=10, max_value=50, value=20, step=10)

api_key = st.sidebar.text_input("Nhập API Key Gemini (Bắt buộc):", type="password", help="Dùng để kích hoạt AI đọc hiểu văn bản")

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
        pdf.cell(200, 8, txt=f"Ten co so: {str(row.get('Tên Cơ Sở', '')).encode('latin-1', 'replace').decode('latin-1')}", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(200, 8, txt=f"Dia chi: {str(row.get('Địa Chỉ', '')).encode('latin-1', 'replace').decode('latin-1')}", ln=True)
        pdf.cell(200, 8, txt=f"SDT: {str(row.get('Số Điện Thoại', ''))}", ln=True)
        
        # Thêm hiển thị mức giá vào PDF
        price_str = f"{row.get('Mức Giá', 0):,} VNĐ" if row.get('Mức Giá', 0) > 0 else "Thỏa thuận / Không rõ"
        pdf.cell(200, 8, txt=f"Muc Gia: {price_str}", ln=True)
        
        pdf.cell(200, 8, txt=f"Nen tang: {str(row.get('Nền Tảng', '')).encode('latin-1', 'replace').decode('latin-1')}", ln=True)
        pdf.multi_cell(0, 8, txt=f"Chi tiet: {str(row.get('Chi Tiết', '')).encode('latin-1', 'replace').decode('latin-1')}")
        pdf.ln(5)
        
    result = pdf.output(dest='S')
    if isinstance(result, str):
        return result.encode('latin-1')
    else:
        return bytes(result)

# --- QUÉT DỮ LIỆU THỰC TẾ ---
def fetch_real_data(kw, loc, cat, time_val, num_res):
    # 3. Cách tìm theo nội dung: Đưa thêm bộ lọc thời gian vào từ khóa để tối ưu kết quả tìm kiếm Google/DuckDuckGo
    time_query = f"trong vòng {time_val} qua" if time_val != "Tất cả" else ""
    search_query = f"{kw} {cat if cat != 'Tất cả' else ''} {loc if loc != 'Toàn quốc' else 'Việt Nam'} báo giá {time_query}"
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=num_res))
        
        raw_text = "\n\n".join([f"Tiêu đề: {r['title']}\nNội dung: {r['body']}\nNguồn: {r['href']}" for r in results])
        return raw_text
    except Exception as e:
        st.error(f"Lỗi khi tìm kiếm web: {e}")
        return ""

# --- LOGIC AI BÓC TÁCH ---
def run_ai_extraction(api_key, raw_text, kw, loc, time_val, req_phone, req_address):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 4. Yêu cầu AI bóc tách thêm cột "Mức Giá" dưới dạng số nguyên để chuẩn bị cho việc sắp xếp
    prompt = f"""
    Bạn là một chuyên gia Data Scraping. Dưới đây là văn bản thô tôi quét được từ internet.
    Hãy lọc và bóc tách các cơ sở, công ty, cửa hàng liên quan đến "{kw}" tại khu vực "{loc}".
    Lưu ý ưu tiên lấy dữ liệu thời gian: "{time_val}".
    
    Điều kiện:
    - Bắt buộc có số điện thoại: {req_phone}
    - Bắt buộc có địa chỉ rõ ràng: {req_address}
    Nếu cơ sở nào không đạt điều kiện, BỎ QUA ngay lập tức.
    
    CHỈ ĐƯỢC PHÉP TRẢ VỀ JSON ARRAY định dạng sau, tuyệt đối không giải thích thêm:
    [
      {{
        "Tên Cơ Sở": "Tên",
        "Địa Chỉ": "Địa chỉ cụ thể",
        "Số Điện Thoại": "SDT",
        "Mức Giá": "Trích xuất giá thành con số nguyên (ví dụ: 150000). Nếu không có giá hoặc để thỏa thuận thì điền số 0",
        "Nền Tảng": "Website/Facebook",
        "Chi Tiết": "Ngắn gọn dịch vụ"
      }}
    ]
    
    Văn bản thô:
    {raw_text[:20000]}
    """
    
    try:
        response = model.generate_content(prompt)
        text_res = response.text
        
        match = re.search(r'\[.*\]', text_res, re.DOTALL)
        if match:
            json_str = match.group(0)
            data = json.loads(json_str)
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi xử lý AI: {e}")
        return pd.DataFrame()

# --- NÚT BẤM ---
if st.sidebar.button("🚀 Quét Dữ Liệu Thực Tế", type="primary"):
    if not keyword:
        st.warning("⚠️ Vui lòng nhập từ khóa tìm kiếm!")
    elif not api_key:
        st.error("⚠️ Vui lòng nhập API Key Gemini để AI có thể bóc tách dữ liệu!")
    else:
        with st.spinner("🔍 BƯỚC 1: Đang cào dữ liệu từ Internet..."):
            raw_data = fetch_real_data(keyword, location, category, time_filter, num_search)
            
        if raw_data:
            with st.spinner("🤖 BƯỚC 2: AI đang đọc, bóc tách Số điện thoại, Địa chỉ và Mức giá..."):
                df_results = run_ai_extraction(api_key, raw_data, keyword, location, time_filter, require_phone, require_address)
                
                if df_results.empty:
                    st.info("ℹ️️ Không tìm thấy cơ sở nào thỏa mãn điều kiện. Hãy thử đổi từ khóa hoặc nới lỏng bộ lọc.")
                else:
                    # 5. Xử lý logic sắp xếp Giá
                    if "Mức Giá" in df_results.columns:
                        # Ép kiểu dữ liệu cột Mức Giá về số để sắp xếp (loại bỏ lỗi nếu AI trả về chuỗi)
                        df_results["Mức Giá"] = pd.to_numeric(df_results["Mức Giá"], errors='coerce').fillna(0)
                        
                        if price_sort == "Từ thấp đến cao":
                            # Bỏ qua các mục có giá trị 0 (không có giá) đẩy xuống cuối nếu muốn, hoặc cứ để mặc định sort
                            df_results = df_results.sort_values(by="Mức Giá", ascending=True).reset_index(drop=True)
                        elif price_sort == "Từ cao đến thấp":
                            df_results = df_results.sort_values(by="Mức Giá", ascending=False).reset_index(drop=True)

                    st.success(f"✅ Thành công! AI đã bóc tách được {len(df_results)} cơ sở thực tế.")
                    st.dataframe(df_results, use_container_width=True)
                    
                    pdf_bytes = export_pdf(df_results, keyword, location)
                    st.download_button(
                        label="📄 Tải Xuống Báo Cáo (PDF)",
                        data=pdf_bytes,
                        file_name=f"Data_Thuc_{keyword.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.error("Không thể lấy dữ liệu từ mạng lúc này.")
