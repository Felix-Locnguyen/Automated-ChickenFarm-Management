"""
crawl_mard.py - Crawler dữ liệu từ Bộ Nông nghiệp

TẠI SAO CẦN FILE NÀY:
- Chatbot cần dữ liệu để trả lời câu hỏi
- Dữ liệu từ mard.gov.vn là nguồn chính thức, đáng tin cậy
- Crawler tự động thu thập, không cần copy thủ công

CẤU TRÚC THƯ MỤC:
09_chatbot/
├── data/
│   ├── raw/          ← HTML gốc từ mard.gov.vn
│   └── processed/    ← Text đã xử lý (sau process_documents.py)
"""

import requests
from bs4 import BeautifulSoup
import time
import os

# ============================================
# CẤU HÌNH
# ============================================

BASE_URL = "https://mard.gov.vn"  # Website chính của Bộ Nông nghiệp

# Các đường dẫn cần cào dữ liệu
# Tại sao chọn các trang này? Vì chúng chứa kiến thức nông nghiệp quan trọng:
SECTIONS = [
    "/tin-tuc-su-kien",           # Tin tức nông nghiệp
    "/chinh-sach",                 # Chính sách, văn bản pháp luật
    "/huong-dan-ky-thuat",        # Hướng dẫn kỹ thuật chăn nuôi
]

# Rate limiting: đợi 1 giây giữa mỗi request
# TẠI SAO: Không spam server của Bộ Nông nghiệp, thể hiện sự chuyên nghiệp
REQUEST_DELAY = 1  # giây

# Thư mục lưu dữ liệu raw
RAW_DIR = "data/raw"


def crawl_page(url: str) -> str:
    """
    Cào một trang web và trả về HTML
    
    TẠI SAO CẦN HÀM NÀY:
    - Tách riêng việc request để dễ quản lý lỗi
    - Nếu một trang lỗi, các trang khác vẫn tiếp tục
    
    NGUYÊN LÝ:
    1. Gửi GET request đến URL
    2. Kiểm tra mã trạng thái (200 = thành công)
    3. Trả về nội dung HTML
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Ném lỗi nếu mã != 200
        response.encoding = 'utf-8'  # Hỗ trợ tiếng Việt
        return response.text
    except requests.RequestException as e:
        print(f"  Lỗi khi cào {url}: {e}")
        return ""


def extract_article_links(html: str, section: str) -> list:
    """
    Trích xuất các link bài viết từ trang danh sách
    
    TẠI SAO CẦN:
    - Mỗi trang danh sách chứa nhiều bài viết
    - Cần tìm URL của từng bài viết để cào chi tiết
    
    NGUYÊN LÝ:
    - Dùng BeautifulSoup parse HTML
    - Tìm tất cả <a> có href chứa đường dẫn bài viết
    """
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    # Tìm các link bài viết (cấu trúc HTML-specific của mard.gov.vn)
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Lọc chỉ lấy link bài viết (chứa /vi/ và kết thúc bằng .aspx)
        if section in href and href.endswith('.aspx'):
            full_url = BASE_URL + href if href.startswith('/') else href
            links.append(full_url)
    
    return list(set(links))  # Loại bỏ link trùng lặp


def extract_content(html: str) -> dict:
    """
    Trích xuất nội dung từ HTML bài viết
    
    TẠI SAO CẦN:
    - HTML chứa nhiều phần không cần thiết (menu, footer, ads)
    - Chỉ cần nội dung bài viết chính
    
    NGUYÊN LÝ:
    - Tìm thẻ <div class="content"> hoặc <article>
    - Bỏ qua script, style, nav, footer
    - Trích xuất text thuần
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Bỏ các thẻ không cần thiết
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()
    
    # Tìm nội dung chính
    content_div = (
        soup.find('div', class_='content') or
        soup.find('div', class_='article-content') or
        soup.find('article') or
        soup.find('div', class_='main-content')
    )
    
    if content_div:
        return {
            'title': soup.title.string if soup.title else "Không có tiêu đề",
            'content': content_div.get_text(separator='\n', strip=True),
            'url': soup.find('link', rel='canonical')['href'] if soup.find('link', rel='canonical') else ""
        }
    
    return {'title': "", 'content': "", 'url': ""}


def save_raw_html(content: dict, filename: str):
    """
    Lưu HTML đã xử lý vào thư mục data/raw/
    
    TẠI SAO LƯU HTML:
    - Cần giữ nguyên format để process_documents.py xử lý sau
    - Có thể cần crawl lại nếu cấu trúc thay đổi
    """
    os.makedirs(RAW_DIR, exist_ok=True)
    filepath = os.path.join(RAW_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Title: {content['title']}\n")
        f.write(f"URL: {content['url']}\n")
        f.write(f"Content:\n{content['content']}")
    
    print(f"  Đã lưu: {filename}")


def crawl_section(section: str, max_pages: int = 50):
    """
    Cào toàn bộ bài viết trong một mục
    
    TẠI SAO CẦN:
    - Mỗi mục (tin tức, chính sách, hướng dẫn) chứa nhiều bài viết
    - Cần duyệt qua từng trang danh sách để tìm bài viết
    
    LIMIT: max_pages = 50
    - Để tránh crawl quá lâu trong lần đầu
    - Có thể tăng sau khi test xong
    """
    print(f"\n=== Đang cào mục: {section} ===")
    
    # Bước 1: Lấy trang danh sách
    list_url = BASE_URL + section
    list_html = crawl_page(list_url)
    
    if not list_html:
        print(f"  Không thể truy cập {list_url}")
        return
    
    # Bước 2: Tìm link các bài viết
    article_links = extract_article_links(list_html, section)
    print(f"  Tìm thấy {len(article_links)} bài viết")
    
    # Bước 3: Cào từng bài viết
    for i, link in enumerate(article_links[:max_pages]):
        print(f"  [{i+1}/{min(len(article_links), max_pages)}] Đang cào: {link}")
        
        article_html = crawl_page(link)
        if article_html:
            content = extract_content(article_html)
            filename = f"{section.replace('/', '_')}_{i:03d}.txt"
            save_raw_html(content, filename)
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)


def main():
    """
    Hàm chính: Cào toàn bộ dữ liệu
    
    THỰC THI:
    python 09_chatbot/scripts/crawl_mard.py
    
    OUTPUT:
    data/raw/
    ├── tin-tuc-su-kien_000.txt
    ├── tin-tuc-su-kien_001.txt
    ├── chinh-sach_000.txt
    ├── huong-dan-ky-thuat_000.txt
    └── ...
    """
    print("=" * 50)
    print("CRAWLER DỮ LIỆU BỘ NÔNG NGHIỆP")
    print("=" * 50)
    
    for section in SECTIONS:
        crawl_section(section)
    
    print("\n" + "=" * 50)
    print("HOÀN THÀNH!")
    print(f"Dữ liệu thô được lưu tại: {RAW_DIR}/")
    print("Bước tiếp theo: python process_documents.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
