# AI Chatbot RAG - Lộ trình Từ Data đến Web

## Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────────┐
│                    LUỒNG DỮ LIỆU & XỬ LÝ                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │   DATA   │───►│ PROCESS  │───►│  TRAIN   │───►│ INGEST   │ │
│  │ (Crawl)  │    │ (Chunk)  │    │ (Embed)  │    │ (Chroma) │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       │                                                    │    │
│       │              ┌────────────────────────────────────┘    │
│       │              │                                          │
│  ┌────▼────┐    ┌────▼────┐    ┌──────────┐    ┌──────────┐  │
│  │  MARD   │    │ CHROMA  │◄──►│  OLLAMA  │◄──►│ FASTAPI  │  │
│  │  Data   │    │   DB    │    │  (LLM)   │    │  Backend │  │
│  └─────────┘    └─────────┘    └──────────┘    └────┬─────┘  │
│                                                      │         │
│                                                 ┌────▼─────┐  │
│                                                 │  REACT   │  │
│                                                 │ Frontend │  │
│                                                 └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Công nghệ sử dụng

| Component | Công nghệ | Lý do chọn |
|-----------|-----------|------------|
| LLM | Ollama (Llama 3.1:8b) | Miễn phí, chạy local, không cần API key |
| Embedding | all-MiniLM-L6-v2 | Miễn phí, nhanh, 384 chiều |
| Vector DB | ChromaDB | Lightweight, chạy local, phù hợp prototype |
| Backend | FastAPI | Tương thích dự án hiện có, async |
| Frontend | React | Đã có trong dự án |

---

## Cấu trúc thư mục mới

```
D:\Share_Projects\Automated-ChickenFarm-Management\
│
├── 02_backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── chatbot.py          # NEW: Chat API endpoints
│   │   ├── services/
│   │   │   └── rag_service.py      # NEW: RAG pipeline service
│   │   └── main.py                 # MODIFY: Include chatbot router
│   │
│   └── requirements.txt            # MODIFY: Add dependencies
│
├── 09_chatbot/                     # NEW: Chatbot module
│   ├── data/
│   │   ├── raw/                    # Raw crawled HTML from mard.gov.vn
│   │   └── processed/              # Processed text chunks
│   │
│   ├── scripts/
│   │   ├── crawl_mard.py           # Crawler for mard.gov.vn
│   │   ├── process_documents.py    # Parse + chunk documents
│   │   └── ingest_to_chroma.py     # Embed + store in ChromaDB
│   │
│   ├── src/
│   │   ├── __init__.py
│   │   ├── config.py               # Configuration (paths, model names)
│   │   ├── loader.py               # Document loader (HTML, PDF)
│   │   ├── chunking.py             # Text chunking strategies
│   │   ├── embeddings.py           # Embedding wrapper
│   │   ├── vector_store.py         # ChromaDB operations
│   │   ├── retriever.py            # Hybrid retrieval
│   │   ├── reranker.py             # Cross-encoder reranker
│   │   ├── llm.py                  # Ollama LLM wrapper
│   │   ├── prompt.py               # Prompt templates
│   │   ├── chain.py                # RAG chain (LCEL)
│   │   └── memory.py               # Conversation memory
│   │
│   ├── tests/
│   │   ├── test_crawler.py
│   │   ├── test_chunking.py
│   │   └── test_rag.py
│   │
│   ├── data_ingestion.ipynb        # Jupyter notebook for data prep
│   ├── requirements.txt            # Chatbot-specific dependencies
│   └── README.md
│
├── 01_frontend/
│   └── 02_src/
│       └── 02_components/
│           └── 02.7_Chatbot/       # NEW: Chatbot UI components
│               ├── ChatBot.jsx
│               ├── ChatMessage.jsx
│               ├── ChatInput.jsx
│               └── ChatBot.css
```

---

## Giai đoạn 1: DATA PREPARATION (Thu thập & Xử lý dữ liệu)

### 1.1 Crawl dữ liệu từ mard.gov.vn

#### File: `09_chatbot/scripts/crawl_mard.py`

**Tại sao tạo file này?**
- Đây là bước đầu tiên và quan trọng nhất: thu thập dữ liệu gốc
- Không có dữ liệu → không có chatbot hoạt động
- Dữ liệu từ Bộ Nông nghiệp Việt Nam là nguồn kiến thức nông nghiệp đáng tin cậy nhất

**Chức năng trong dự án:**
- Cào dữ liệu tin tức, chính sách, hướng dẫn kỹ thuật từ `mard.gov.vn`
- Lưu trữ raw HTML vào thư mục `data/raw/`
- Có cơ chế rate limiting để không spam server

```python
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
```

---

### 1.2 Xử lý Documents

#### File: `09_chatbot/scripts/process_documents.py`

**Tại sao tạo file này?**
- Raw HTML chưa thể dùng trực tiếp cho AI
- Cần chuyển HTML → Text thuần → Chia thành chunks nhỏ
- Chunks nhỏ giúp AI tìm kiếm và trả lời chính xác hơn

**Chức năng trong dự án:**
- Parse HTML, trích xuất text thuần
- Chia text thành các đoạn nhỏ (chunks) có overlap
- Lưu metadata (tiêu đề, nguồn) để trích dẫn sau này

```python
"""
process_documents.py - Xử lý tài liệu

TẠI SAO CẦN FILE NÀY:
1. Raw HTML chưa thể dùng cho AI (quá nhiều tag, script, style)
2. Text quá dài → AI không thể xử lý hết (token limit)
3. Cần chia nhỏ thành chunks để tìm kiếm chính xác hơn
4. Cần lưu metadata (tiêu đề, nguồn) để trích dẫn

NGUYÊN LÝ RAG:
- Không đưa toàn bộ tài liệu cho AI (quá dài, tốn token)
- Chia thành chunks nhỏ (500-1000 từ)
- Khi user hỏi, tìm chunks liên quan nhất
- Chỉ đưa chunks liên quan cho AI → chính xác, tiết kiệm

CHIẾN LƯỢC CHUNKING:
- chunk_size: 1000 ký tự (không quá ngắn, không quá dài)
- chunk_overlap: 200 ký tự (giữ liên tục ngữ cảnh)
- separators: ["\n\n", "\n", ". ", " "] (chia theo đoạn → câu → từ)
"""

from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import json

# ============================================
# CẤU HÌNH
# ============================================

RAW_DIR = "data/raw"           # Thư mục chứa HTML thô
PROCESSED_DIR = "data/processed"  # Thư mục chứa chunks đã xử lý

# Cấu hình chunking
CHUNK_SIZE = 1000      # Kích thước mỗi chunk (ký tự)
CHUNK_OVERLAP = 200    # Số ký tự overlap giữa các chunk


def parse_html_file(filepath: str) -> dict:
    """
    Parse file HTML và trích xuất text
    
    TẠI SAO CẦN:
    - HTML gốc chứa nhiều tag không cần thiết
    - Cần trích xuất chỉ nội dung văn bản
    
    NGUYÊN LÝ:
    1. Đọc file HTML
    2. Dùng BeautifulSoup parse
    3. Bỏ qua script, style, nav, footer
    4. Tìm div.content hoặc article
    5. Trả về text thuần + metadata
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse metadata từ header file
    lines = content.split('\n')
    title = ""
    url = ""
    body_start = 0
    
    for i, line in enumerate(lines):
        if line.startswith('Title:'):
            title = line.replace('Title:', '').strip()
        elif line.startswith('URL:'):
            url = line.replace('URL:', '').strip()
        elif line.startswith('Content:'):
            body_start = i + 1
            break
    
    body = '\n'.join(lines[body_start:])
    
    return {
        'title': title,
        'url': url,
        'content': body,
        'source': filepath
    }


def chunk_text(text: str, metadata: dict) -> list:
    """
    Chia text thành các chunks nhỏ
    
    TẠI SAO CẦN CHUNKS:
    1. Text dài → không vừa token limit của LLM (~4000 tokens)
    2. Chunks nhỏ → tìm kiếm chính xác hơn
    3. Mỗi chunk là một "đoạn kiến thức" độc lập
    
    CHUNK_SIZE = 1000:
    - Quá ngắn (< 200): Mất ngữ cảnh, thiếu thông tin
    - Quá dài (> 2000): Khó tìm chính xác, tốn token
    - 1000 là hợp lý cho văn bản tiếng Việt
    
    CHUNK_OVERLAP = 200:
    - Không overlap: Mất thông tin ở ranh giới chunk
    - Quá nhiều overlap (> 500): Trùng lặp, tốn dung lượng
    - 200 ký tự đủ giữ liên tục ngữ cảnh
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",      # Ưu tiên chia theo đoạn
            "\n",        # Sau đó theo dòng
            ". ",        # Sau đó theo câu
            " ",         # Cuối cùng theo từ
            ""           # Nếu vẫn quá dài, cắt ký tự
        ],
        length_function=len,  # Đo độ dài bằng ký tự
    )
    
    chunks = splitter.split_text(text)
    
    # Thêm metadata cho mỗi chunk
    result = []
    for i, chunk in enumerate(chunks):
        result.append({
            'text': chunk,
            'metadata': {
                'title': metadata['title'],
                'source': metadata['source'],
                'url': metadata['url'],
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
        })
    
    return result


def process_all():
    """
    Xử lý toàn bộ file trong data/raw/
    
    QUY TRÌNH:
    1. Đọc từng file HTML từ data/raw/
    2. Parse HTML → trích xuất text + metadata
    3. Chia text thành chunks
    4. Lưu chunks vào data/processed/
    
    OUTPUT:
    data/processed/
    ├── chunks_000.json    ← Chunks từ file đầu tiên
    ├── chunks_001.json    ← Chunks từ file thứ hai
    └── ...
    
    Mỗi file JSON chứa:
    {
        "chunks": [
            {"text": "...", "metadata": {...}},
            ...
        ]
    }
    """
    print("=" * 50)
    print("XỬ LÝ TÀI LIỆU")
    print("=" * 50)
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    all_chunks = []
    files = [f for f in os.listdir(RAW_DIR) if f.endswith('.txt')]
    
    print(f"Tìm thấy {len(files)} file cần xử lý")
    
    for i, filename in enumerate(files):
        print(f"\n[{i+1}/{len(files)}] Đang xử lý: {filename}")
        
        filepath = os.path.join(RAW_DIR, filename)
        doc = parse_html_file(filepath)
        
        if not doc['content']:
            print(f"  Bỏ qua: Không có nội dung")
            continue
        
        # Chunks
        chunks = chunk_text(doc['content'], doc['metadata'])
        all_chunks.extend(chunks)
        
        print(f"  Tạo được {len(chunks)} chunks")
    
    # Lưu tất cả chunks
    output_path = os.path.join(PROCESSED_DIR, "all_chunks.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_chunks': len(all_chunks),
            'chunks': all_chunks
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 50}")
    print(f"HOÀN THÀNH!")
    print(f"Tổng cộng: {len(all_chunks)} chunks")
    print(f"Lưu tại: {output_path}")
    print(f"Bước tiếp theo: python ingest_to_chroma.py")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    process_all()
```

---

### 1.3 Embedding & Lưu vào Vector Database

#### File: `09_chatbot/scripts/ingest_to_chroma.py`

**Tại sao tạo file này?**
- Text chunks chưa thể tìm kiếm bằng AI
- Cần chuyển chunks thành vectors (số) để AI hiểu và so sánh
- ChromaDB lưu vectors để tìm kiếm nhanh khi user hỏi

**Chức năng trong dự án:**
- Load embedding model (all-MiniLM-L6-v2)
- Embed each chunk thành vector
- Lưu vào ChromaDB để tìm kiếm sau này

```python
"""
ingest_to_chroma.py - Embed và lưu vào Vector Database

TẠI SAO CẦN FILE NÀY:
1. AI không hiểu text trực tiếp, chỉ hiểu số (vectors)
2. Embedding chuyển text → vector (dãy số) giữ nguyên ý nghĩa
3. ChromaDB lưu vectors để tìm kiếm nhanh
4. Khi user hỏi, query cũng được embed → tìm vectors gần nhất

NGUYÊN LÝ EMBEDDING:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Text       │ ──► │ Embed Model │ ──► │   Vector    │
│ "Nuôi gà"  │     │ MiniLM-L6   │     │ [0.2, -0.1, │
│             │     │             │     │  0.5, ...]  │
└─────────────┘     └─────────────┘     └─────────────┘

- Text giống nhau → Vector gần nhau
- "Nuôi gà" và "chăn nuôi gia cầm" → vectors gần nhau
- "Nuôi gà" và "cây lúa" → vectors xa nhau

NGUYÊN LÝ TÌM KIẾM:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Query      │ ──► │ Embed Query │ ──► │ Tìm top-k   │
│ "Cách nuôi  │     │ [0.2, -0.1, │     │ vectors gần │
│  gà thịt"  │     │  0.5, ...]  │     │ nhất        │
└─────────────┘     └─────────────┘     └─────────────┘

all-MiniLM-L6-v2:
- Model miễn phí, chạy local
- 384 chiều (vector có 384 số)
- Nhanh, phù hợp prototype
- Hỗ trợ tiếng Việt ở mức cơ bản
"""

import chromadb
from sentence_transformers import SentenceTransformer
import json
import os

# ============================================
# CẤU HÌNH
# ============================================

PROCESSED_DIR = "data/processed"     # Thư mục chứa chunks
CHROMA_DIR = "./chroma_db"           # Thư mục lưu ChromaDB
COLLECTION_NAME = "mard_documents"   # Tên collection trong ChromaDB

# Model embedding
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Model miễn phí từ HuggingFace


def load_chunks(filepath: str) -> list:
    """
    Load chunks từ file JSON
    
    TẠI SAO CẦN:
    - Chunks đã được tạo ở process_documents.py
    - Cần load vào memory để embed
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['chunks']


def create_or_get_collection(client):
    """
    Tạo hoặc lấy collection từ ChromaDB
    
    COLLECTION LÀ GÌ?
    - Tương tự "table" trong SQL
    - Lưu trữ vectors + metadata + documents
    - Mỗi collection là một "cơ sở kiến thức" riêng
    
    TẠI SAO DÙNG "mard_documents"?
    - Đặt tên rõ ràng để dễ quản lý
    - Nếu có nhiều nguồn data, tạo collection riêng
    """
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Tài liệu Bộ Nông nghiệp Việt Nam"}
    )


def ingest():
    """
    Quy trình ingest:
    1. Load embedding model
    2. Kết nối ChromaDB
    3. Load chunks
    4. Embed từng chunk
    5. Lưu vào collection
    
    THỜI GIAN DỰ KIẾN:
    - 100 chunks: ~2 giây
    - 1000 chunks: ~15 giây
    - 10000 chunks: ~2 phút
    """
    print("=" * 50)
    print("INGEST DỮ LIỆU VÀO CHROMADB")
    print("=" * 50)
    
    # Bước 1: Load embedding model
    print("\n[1/4] Đang load embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"  Model: {EMBEDDING_MODEL}")
    print(f"  Chiều vector: {model.get_sentence_embedding_dimension()}")
    
    # Bước 2: Kết nối ChromaDB
    print("\n[2/4] Đang kết nối ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = create_or_get_collection(client)
    print(f"  Collection: {COLLECTION_NAME}")
    
    # Bước 3: Load chunks
    print("\n[3/4] Đang load chunks...")
    chunks_path = os.path.join(PROCESSED_DIR, "all_chunks.json")
    chunks = load_chunks(chunks_path)
    print(f"  Số chunks: {len(chunks)}")
    
    # Bước 4: Embed và lưu
    print("\n[4/4] Đang embed và lưu vào ChromaDB...")
    
    # Chuẩn bị data cho ChromaDB
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
        # Embed text
        embedding = model.encode(chunk['text'])
        
        # Chuẩn bị data
        ids.append(f"doc_{i}")
        embeddings.append(embedding.tolist())
        documents.append(chunk['text'])
        metadatas.append(chunk['metadata'])
        
        # Hiển thị tiến trình
        if (i + 1) % 100 == 0:
            print(f"  Đã embed: {i + 1}/{len(chunks)} chunks")
    
    # Lưu vào ChromaDB
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"\n{'=' * 50}")
    print(f"HOÀN THÀNH!")
    print(f"Tổng cộng: {len(chunks)} chunks đã lưu")
    print(f"ChromaDB: {CHROMA_DIR}")
    print(f"Bước tiếp theo: python 02_backend/run.py (khởi động backend)")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    ingest()
```

---

## Giai đoạn 2: BACKEND API (FastAPI + RAG Pipeline)

### 2.1 RAG Service

#### File: `02_backend/app/services/rag_service.py`

**Tại sao tạo file này?**
- Đây là "bộ não" của chatbot
- Kết nối tất cả: Embedding → ChromaDB → Ollama LLM → Response
- Tách riêng service để dễ test và维护

**Chức năng trong dự án:**
- Retrieve: Tìm chunks liên quan từ ChromaDB
- Generate: Tạo câu trả lời bằng Ollama LLM
- Memory: Quản lý lịch sử trò chuyện

```python
"""
rag_service.py - RAG Pipeline Service

TẠI SAO CẦN FILE NÀY:
1. Đây là "bộ não" của chatbot
2. Kết nối tất cả component: Embedding, ChromaDB, Ollama
3. Tách riêng để dễ test,维护, thay đổi
4. Có thể tái sử dụng cho các chatbot khác

NGUYÊN LÝ RAG (Retrieval-Augmented Generation):
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User Query │ ──► │  Retrieve   │ ──► │  Generate   │
│ "Cách nuôi  │     │ Tìm chunks  │     │ Tạo câu trả │
│  gà thịt"  │     │ liên quan   │     │ lời với LLM │
└─────────────┘     └─────────────┘     └─────────────┘

BƯỚC 1 - RETRIEVE:
1. Embed query thành vector
2. Tìm top-k vectors gần nhất trong ChromaDB
3. Trả về chunks + metadata

BƯỚC 2 - GENERATE:
1. Tạo prompt với context (chunks) + question
2. Gửi đến Ollama LLM
3. LLM tạo câu trả lời dựa trên context

TẠI SAO KHÔNG CHỈ DÙNG LLM?
- LLM chỉ biết kiến thức đến ngày training
- RAG bổ sung kiến thức thực tế từ dữ liệu
- Luôn có nguồn trích dẫn khi trả lời
"""

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
import os


class RAGService:
    """
    RAG Service - Xử lý chat với RAG
    
    TẠI SAO DÙNG CLASS?
    - Tách biệt logic business
    - Dễ inject dependency (test, thay đổi component)
    - Singleton pattern: chỉ load model 1 lần
    
    CÁC COMPONENT:
    1. Embedding Model: all-MiniLM-L6-v2 (chuyển text → vector)
    2. ChromaDB: Lưu vectors, tìm kiếm nhanh
    3. LLM: Ollama (Llama 3.1 hoặc Qwen2.5)
    4. Prompt: Hướng dẫn LLM trả lời
    """
    
    def __init__(self):
        """
        Khởi tạo RAG Service
        
        TẠI SAO KHỞI TẠO TRONG __init__?
        - Chỉ load model 1 lần (không load lại mỗi request)
        - Tiết kiệm tài nguyên
        - Nhanh hơn khi serving
        """
        print("Đang khởi tạo RAG Service...")
        
        # 1. Load Embedding Model
        # TẠI SAO all-MiniLM-L6-v2?
        # - Miễn phí, chạy local
        # - 384 chiều, nhanh
        # - Phù hợp cho prototype
        print("  [1/3] Đang load embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 2. Kết nối ChromaDB
        # TẠI SAO PersistentClient?
        # - Lưu dữ liệu xuống disk (không mất khi restart)
        # - Dùng ./chroma_db để dễ quản lý
        print("  [2/3] Đang kết nối ChromaDB...")
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(
            name="mard_documents"
        )
        
        # 3. Kết nối Ollama LLM
        # TẠI SAO Ollama?
        # - Miễn phí, chạy local
        # - Không cần API key
        # - Hỗ trợ nhiều model: Llama 3.1, Qwen2.5, etc.
        # TẠI SAO Llama 3.1:8b?
        # - 8B params: vừa đủ thông minh, vừa chạy được trên PC
        # - Hỗ trợ tiếng Việt tốt
        print("  [3/3] Đang kết nối Ollama...")
        self.llm = Ollama(model="llama3.1:8b")
        
        print("  ✓ RAG Service sẵn sàng!")
    
    def retrieve(self, query: str, top_k: int = 4) -> tuple:
        """
        Retrieve: Tìm chunks liên quan từ ChromaDB
        
        TẠI SAO top_k = 4?
        - Quá ít (< 3): Thiếu thông tin, câu trả lời không đủ
        - Quá nhiều (> 8): Quá nhiều context, LLM bị confusing
        - 4 là hợp lý: đủ thông tin, không quá tải
        
        NGUYÊN LÝ:
        1. Embed query thành vector
        2. Tìm top-k vectors gần nhất (cosine similarity)
        3. Trả về chunks + metadata
        
        OUTPUT:
        - documents: List text chunks
        - metadatas: List metadata (title, source, url)
        """
        # Embed query
        query_embedding = self.embedding_model.encode(query)
        
        # Tìm trong ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        return results['documents'][0], results['metadatas'][0]
    
    def generate(self, query: str, context: str) -> str:
        """
        Generate: Tạo câu trả lời bằng Ollama LLM
        
        TẠI SAO CẦN PROMPT?
        - Hướng dẫn LLM trả lời như thế nào
        - Đặt context (chunks từ ChromaDB)
        - Yêu cầu trích dẫn nguồn
        
        STRUCTURE PROMPT:
        1. System message: Vai trò + instructions
        2. Context: Chunks từ database
        3. Human message: Câu hỏi của user
        
        TẠI SAO temperature = 0.3?
        - Quá thấp (0.0): Quá cứng nhắc, không sáng tạo
        - Quá cao (0.8): Quá tự do, có thể bịa
        - 0.3: Đúng facts, nhưng linh hoạt ngôn từ
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Bạn là trợ lý AI chuyên về nông nghiệp Việt Nam.

NHIỆM VỤ:
- Trả lời câu hỏi dựa trên context được cung cấp
- Luôn trích dẫn nguồn khi có thể
- Nếu context không đủ thông tin, nói rõ
- Trả lời bằng tiếng Việt, dễ hiểu

NGUYÊN TẮC:
1. Chỉ dùng thông tin từ context, không bịa
2. Nếu có nhiều nguồn, liệt kê tất cả
3. Nếu câu hỏi ngoài phạm vi, nói rõ

Context từ Bộ Nông nghiệp:
{context}"""),
            ("human", "{question}")
        ])
        
        # Tạo chain
        chain = prompt | self.llm | StrOutputParser()
        
        # Invoke
        return chain.invoke({
            "context": context,
            "question": query
        })
    
    def chat(self, query: str) -> dict:
        """
        Chat: Full RAG pipeline
        
        QUY TRÌNH:
        1. Retrieve: Tìm chunks liên quan
        2. Generate: Tạo câu trả lời với LLM
        3. Format: Trả về answer + sources
        
        OUTPUT:
        {
            "answer": "Cách nuôi gà thịt...",
            "sources": [
                {"text": "...", "metadata": {"title": "...", "source": "..."}}
            ]
        }
        """
        # Retrieve
        documents, metadatas = self.retrieve(query)
        
        # Format context
        context = "\n\n---\n\n".join(documents)
        
        # Generate
        answer = self.generate(query, context)
        
        # Format sources
        sources = [
            {"text": doc, "metadata": meta}
            for doc, meta in zip(documents, metadatas)
        ]
        
        return {
            "answer": answer,
            "sources": sources
        }


# Singleton instance
_rag_service = None


def get_rag_service() -> RAGService:
    """
    Get RAG Service instance (Singleton)
    
    TẠI SAO DÙNG SINGLETON?
    - Chỉ load model 1 lần
    - Tiết kiệm memory
    - Nhanh hơn khi serving
    
    CÁCH DÙNG:
    service = get_rag_service()
    result = service.chat("Cách nuôi gà?")
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
```

---

### 2.2 Chat API

#### File: `02_backend/app/api/chatbot.py`

**Tại sao tạo file này?**
- Frontend cần gọi API để chat
- Tách API riêng để dễ quản lý
- Tuân theo cấu trúc API đã có trong dự án

**Chức năng trong dự án:**
- POST `/api/chat`: Gửi message, nhận response
- POST `/api/chat/stream`: Streaming response (SSE)

```python
"""
chatbot.py - Chat API Endpoints

TẠI SAO TẠO FILE NÀY?
1. Frontend cần gọi API để chat
2. Tuân theo cấu trúc API đã có (environment.py, feeding.py, etc.)
3. Tách riêng để dễ quản lý, test

API ENDPOINTS:
- POST /api/chat: Gửi message, nhận response
- POST /api/chat/stream: Streaming response (SSE)

TẠI SAO CẦN STREAMING?
- LLM mất 2-5 giây để tạo câu trả lời
- Không streaming: User phải đợi 2-5 giây rồi thấy response
- Có streaming: User thấy từng từ xuất hiện real-time
- Giống ChatGPT: từ từ hiện từng chữ
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from ..services.rag_service import get_rag_service

router = APIRouter()


# ============================================
# REQUEST/RESPONSE SCHEMAS
# ============================================

class ChatRequest(BaseModel):
    """
    Schema cho chat request
    
    TẠI SAO DÙNG PYDANTIC?
    - Validate dữ liệu đầu vào
    - Tự động tạo documentation
    - Tự động lỗi nếu thiếu trường
    
    VÍ DỤ:
    {
        "message": "Cách nuôi gà thịt?",
        "session_id": "user123"
    }
    """
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=1000,
        description="Câu hỏi của user"
    )
    session_id: Optional[str] = Field(
        default="default",
        description="ID phiên làm việc (để nhớ lịch sử)"
    )


class SourceResponse(BaseModel):
    """
    Schema cho source (nguồn)
    
    TẠI SAO CẦN SOURCE?
    - User cần biết thông tin từ đâu
    - Đảm bảo tính minh bạch
    - Giống ChatGPT: "Theo nguồn..."
    """
    text: str = Field(description="Text chunk từ database")
    metadata: dict = Field(description="Metadata (title, source, url)")


class ChatResponse(BaseModel):
    """
    Schema cho chat response
    
    TẠI SAO CẦN SCHEMA?
    - Frontend biết chính xác response format
    - Dễ test, debug
    - Tự động tạo Swagger documentation
    """
    answer: str = Field(description="Câu trả lời từ AI")
    sources: List[SourceResponse] = Field(description="Nguồn trích dẫn")


# ============================================
# API ENDPOINTS
# ============================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    POST /api/chat - Gửi message, nhận response
    
    TẠI SAO DÙNG POST?
    - POST dùng để gửi dữ liệu lên server
    - Không nên dùng GET vì query có thể dài
    
    TẠI SAO ASYNC?
    - LLM call mất 2-5 giây
    - Async cho phép server xử lý request khác trong lúc chờ
    - Không block thread chính
    """
    try:
        # Get RAG service
        service = get_rag_service()
        
        # Chat
        result = service.chat(request.message)
        
        # Format response
        sources = [
            SourceResponse(
                text=source['text'],
                metadata=source['metadata']
            )
            for source in result['sources']
        ]
        
        return ChatResponse(
            answer=result['answer'],
            sources=sources
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xử lý chat: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    POST /api/chat/stream - Streaming response (SSE)
    
    STREAMING LÀ GÌ?
    - Server gửi response từng phần (từng từ)
    - Frontend hiển thị real-time
    - Giống ChatGPT: từ từ hiện từng chữ
    
    SSE LÀ GÌ?
    - Server-Sent Events
    - Protocol chuẩn cho streaming từ server → client
    - Frontend dùng EventSource API để nhận
    
    OUTPUT FORMAT:
    data: {"token": "Cách"}
    data: {"token": " nuôi"}
    data: {"token": " gà"}
    ...
    data: [DONE]
    """
    try:
        service = get_rag_service()
        
        async def generate():
            # Retrieve context
            documents, metadatas = service.retrieve(request.message)
            context = "\n\n---\n\n".join(documents)
            
            # Stream from Ollama
            for chunk in service.llm.stream(
                f"""Bạn là trợ lý AI chuyên về nông nghiệp Việt Nam.

Context:
{context}

Câu hỏi: {request.message}

Trả lời:"""
            ):
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi stream chat: {str(e)}"
        )
```

---

### 2.3 Cập nhật main.py

#### File: `02_backend/app/main.py` (thêm router)

```python
# Thêm dòng này vào file main.py hiện tại
from .api import chatbot

# Thêm router (thêm sau các router hiện có)
app.include_router(chatbot.router, prefix="/api", tags=["chatbot"])
```

---

## Giai đoạn 3: FRONTEND INTEGRATION (React Chat UI)

### 3.1 ChatBot Component

#### File: `01_frontend/02_src/02_components/02.7_Chatbot/ChatBot.jsx`

**Tại sao tạo file này?**
- Đây là component chính của chat UI
- Quản lý tin nhắn, trạng thái loading
- Gọi API backend để chat

**Chức năng trong dự án:**
- Hiển thị lịch sử tin nhắn
- Gửi tin nhắn đến backend
- Hiển thị response real-time
- Hiển thị nguồn trích dẫn

```jsx
/**
 * ChatBot.jsx - Component chính của Chat UI
 * 
 * TẠI SAO TẠO FILE NÀY?
 * 1. Đây là "mặt tiền" của chatbot
 * 2. Quản lý state: tin nhắn, loading, error
 * 3. Gọi API backend
 * 4. Hiển thị giao diện chat
 * 
 * CẤU TRÚC:
 * ┌─────────────────────────────┐
 * │  ChatBot Header (🤖 AI)    │
 * ├─────────────────────────────┤
 * │  Messages Container         │
 * │  ├── ChatMessage (user)     │
 * │  ├── ChatMessage (AI)       │
 * │  └── ...                    │
 * ├─────────────────────────────┤
 * │  ChatInput (gõ tin nhắn)    │
 * └─────────────────────────────┘
 * 
 * STATE:
 * - messages: Mảng tin nhắn
 * - isLoading: Đang chờ AI trả lời
 * - error: Lỗi (nếu có)
 */

import { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import './ChatBot.css';

export default function ChatBot() {
  // ============================================
  // STATE MANAGEMENT
  // ============================================
  
  /**
   * messages: Mảng chứa lịch sử tin nhắn
   * 
   * MỖI MESSAGE CÓ STRUCTURE:
   * {
   *   role: 'user' | 'assistant',
   *   content: 'Nội dung tin nhắn',
   *   sources: [...] // Chỉ có ở response AI
   * }
   * 
   * TẠI SAO DÙNG STATE ARRAY?
   * - Để hiển thị lịch sử chat
   * - Để gửi kèm khi cần context
   */
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Xin chào! Tôi là trợ lý AI chuyên về nông nghiệp. Bạn có câu hỏi gì về chăn nuôi gia cầm không?',
      sources: []
    }
  ]);
  
  /**
   * isLoading: Đang chờ AI trả lời
   * 
   * TẠI SAO CẦN?
   * - Hiển thị loading spinner
   * - Disable input khi đang chờ
   * - Prevent duplicate requests
   */
  const [isLoading, setIsLoading] = useState(false);
  
  /**
   * error: Lỗi (nếu có)
   * 
   * TẠI SAO CẦN?
   * - Hiển thị thông báo lỗi
   * - Giúp debug khi có vấn đề
   */
  const [error, setError] = useState(null);
  
  /**
   * messagesEndRef: Ref để scroll xuống cuối
   * 
   * TẠI SAO CẦN?
   * - Khi có tin nhắn mới, tự động scroll xuống
   * - Giống chat app thông thường
   */
  const messagesEndRef = useRef(null);
  
  // ============================================
  // EFFECTS
  // ============================================
  
  /**
   * Auto-scroll khi có tin nhắn mới
   * 
   * TẠI SAO DÙNG useEffect?
   * - Mỗi khi messages thay đổi, scroll xuống cuối
   * - Tạo cảm giác chat real-time
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // ============================================
  // HANDLERS
  // ============================================
  
  /**
   * handleSend: Gửi tin nhắn
   * 
   * QUY TRÌNH:
   * 1. Thêm tin nhắn user vào messages
   * 2. Set isLoading = true
   * 3. Gọi API backend
   * 4. Thêm response AI vào messages
   * 5. Set isLoading = false
   * 
   * TẠI SAO CẦN TRY-CATCH?
   * - Bắt lỗi network
   * - Bắt lỗi server
   * - Hiển thị lỗi cho user
   */
  const handleSend = async (message) => {
    if (!message.trim() || isLoading) return;
    
    // Thêm tin nhắn user
    const userMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    
    try {
      // Gọi API backend
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Thêm response AI
      const aiMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources
      };
      setMessages(prev => [...prev, aiMessage]);
      
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message);
      
      // Thêm tin nhắn lỗi
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Xin lỗi, có lỗi xảy ra: ${err.message}. Vui lòng thử lại sau.`,
        sources: []
      }]);
      
    } finally {
      setIsLoading(false);
    }
  };
  
  // ============================================
  // RENDER
  // ============================================
  
  return (
    <div className="chatbot-container">
      {/* Header */}
      <div className="chatbot-header">
        <span className="chatbot-icon">🤖</span>
        <span className="chatbot-title">Trợ lý Nông nghiệp</span>
        <span className="chatbot-badge">AI</span>
      </div>
      
      {/* Messages */}
      <div className="chatbot-messages">
        {messages.map((msg, index) => (
          <ChatMessage key={index} message={msg} />
        ))}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="chat-loading">
            <span className="typing-dot">●</span>
            <span className="typing-dot">●</span>
            <span className="typing-dot">●</span>
          </div>
        )}
        
        {/* Error message */}
        {error && (
          <div className="chat-error">
            ⚠️ {error}
          </div>
        )}
        
        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <ChatInput onSend={handleSend} isLoading={isLoading} />
    </div>
  );
}
```

---

### 3.2 ChatMessage Component

#### File: `01_frontend/02_src/02_components/02.7_Chatbot/ChatMessage.jsx`

**Tại sao tạo file này?**
- Tách riêng message component để tái sử dụng
- Dễ quản lý styling cho user vs AI message
- Hiển thị sources (nguồn trích dẫn)

```jsx
/**
 * ChatMessage.jsx - Hiển thị một tin nhắn
 * 
 * TẠI SAO TẠO FILE NÀY?
 * 1. Tách riêng để tái sử dụng
 * 2. Dễ quản lý styling: user (phải), AI (trái)
 * 3. Hiển thị sources (nguồn trích dẫn)
 * 
 * PROPS:
 * - message: { role, content, sources }
 * 
 * STYLING:
 * - User message: Nền xanh, căn phải
 * - AI message: Nền kem, căn trái
 * - Sources: Hiển thị bên dưới AI message
 */

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  
  return (
    <div className={`chat-message ${isUser ? 'user' : 'assistant'}`}>
      {/* Avatar */}
      <div className="chat-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      
      {/* Content */}
      <div className="chat-content">
        {/* Bubble */}
        <div className={`chat-bubble ${isUser ? 'user-bubble' : 'ai-bubble'}`}>
          {message.content}
        </div>
        
        {/* Sources (chỉ hiển thị cho AI message) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="chat-sources">
            <span className="sources-label">📎 Nguồn:</span>
            {message.sources.map((source, index) => (
              <span key={index} className="source-tag">
                {source.metadata?.title || 'Tài liệu Bộ Nông nghiệp'}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

---

### 3.3 ChatInput Component

#### File: `01_frontend/02_src/02_components/02.7_Chatbot/ChatInput.jsx`

**Tại sao tạo file này?**
- Tách input để tái sử dụng
- Quản lý state input riêng
- Xử lý Enter key để gửi

```jsx
/**
 * ChatInput.jsx - Input box để nhập tin nhắn
 * 
 * TẠI SAO TẠO FILE NÀY?
 * 1. Tách riêng để tái sử dụng
 * 2. Quản lý state input riêng
 * 3. Xử lý Enter key để gửi
 * 4. Hiển thị loading state
 * 
 * PROPS:
 * - onSend: Function gọi khi gửi tin nhắn
 * - isLoading: Đang chờ AI trả lời
 */

import { useState } from 'react';

export default function ChatInput({ onSend, isLoading }) {
  const [input, setInput] = useState('');
  
  /**
   * handleKeyPress: Xử lý phím tắt
   * 
   * TẠI SAO CẦN?
   * - Enter để gửi tin nhắn (giống chat app)
   * - Shift+Enter để xuống dòng (không gửi)
   */
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  
  /**
   * handleSend: Gửi tin nhắn
   * 
   * TẠI SAO CẦN CHECK?
   * - Không gửi nếu input rỗng
   * - Không gửi nếu đang loading
   */
  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSend(input.trim());
      setInput('');
    }
  };
  
  return (
    <div className="chat-input-container">
      <textarea
        className="chat-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Nhập câu hỏi về nông nghiệp..."
        disabled={isLoading}
        rows={1}
      />
      <button
        className={`chat-send-btn ${isLoading ? 'loading' : ''}`}
        onClick={handleSend}
        disabled={isLoading || !input.trim()}
      >
        {isLoading ? '⏳' : '➤'}
      </button>
    </div>
  );
}
```

---

### 3.4 CSS Styling

#### File: `01_frontend/02_src/02_components/02.7_Chatbot/ChatBot.css`

**Tại sao tạo file này?**
- Styling cho toàn bộ chat UI
- Tách CSS riêng để dễ quản lý
- Responsive design cho mobile

```css
/* ============================================
   CHATBOT STYLES
   ============================================ */

/* Container chính */
.chatbot-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 800px;
  margin: 0 auto;
  background-color: #fff8f0;
  border: 2px solid #d4a574;
  border-radius: 16px;
  overflow: hidden;
}

/* Header */
.chatbot-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: #654321;
  color: white;
  font-weight: 700;
}

.chatbot-icon {
  font-size: 20px;
}

.chatbot-title {
  flex: 1;
}

.chatbot-badge {
  background-color: #16a34a;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 10px;
}

/* Messages container */
.chatbot-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Message */
.chat-message {
  display: flex;
  gap: 8px;
  max-width: 80%;
}

.chat-message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.chat-message.assistant {
  align-self: flex-start;
}

/* Avatar */
.chat-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.chat-message.user .chat-avatar {
  background-color: #3b82f6;
}

.chat-message.assistant .chat-avatar {
  background-color: #16a34a;
}

/* Bubble */
.chat-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.user-bubble {
  background-color: #3b82f6;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-bubble {
  background-color: #fff;
  border: 1px solid #e8d9ca;
  border-bottom-left-radius: 4px;
}

/* Sources */
.chat-sources {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.sources-label {
  font-size: 10px;
  color: #a0826d;
}

.source-tag {
  font-size: 10px;
  padding: 2px 6px;
  background-color: #fef3c7;
  color: #92400e;
  border-radius: 4px;
}

/* Loading */
.chat-loading {
  display: flex;
  gap: 4px;
  padding: 10px 14px;
  background-color: #fff;
  border: 1px solid #e8d9ca;
  border-radius: 12px;
  width: fit-content;
}

.typing-dot {
  animation: typing 1.4s infinite;
  color: #a0826d;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; }
  30% { opacity: 1; }
}

/* Error */
.chat-error {
  padding: 10px 14px;
  background-color: #fee2e2;
  color: #dc2626;
  border-radius: 12px;
  font-size: 13px;
  text-align: center;
}

/* Input */
.chat-input-container {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #e8d9ca;
  background-color: #fff;
}

.chat-input {
  flex: 1;
  padding: 10px 12px;
  border: 2px solid #d4a574;
  border-radius: 12px;
  font-size: 14px;
  resize: none;
  outline: none;
  font-family: inherit;
}

.chat-input:focus {
  border-color: #654321;
}

.chat-input:disabled {
  background-color: #f5f5f5;
}

.chat-send-btn {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 12px;
  background-color: #654321;
  color: white;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
}

.chat-send-btn:hover:not(:disabled) {
  background-color: #543210;
}

.chat-send-btn:disabled {
  background-color: #d1d5db;
  cursor: not-allowed;
}

.chat-send-btn.loading {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
```

---

### 3.5 Cập nhật Dashboard.jsx

#### File: `01_frontend/02_src/03_pages/Dashboard.jsx` (thêm ChatBot)

```jsx
// Thêm import
import ChatBot from '../02_components/02.7_Chatbot/ChatBot.jsx';

// Trong return, sau CoopsList
<h3 className="section-title">🤖 Trợ lý Nông nghiệp</h3>
<div style={{ height: '400px' }}>
  <ChatBot />
</div>
```

---

## Quy trình thực hiện

### Bước 1: Cài đặt Ollama

```bash
# Download Ollama từ https://ollama.ai
# Sau đó chạy lệnh:
ollama pull llama3.1:8b
```

### Bước 2: Cài đặt dependencies

```bash
# Chatbot dependencies
cd 09_chatbot
pip install -r requirements.txt

# Backend dependencies
cd 02_backend
pip install -r requirements.txt
```

### Bước 3: Crawl dữ liệu

```bash
cd 09_chatbot
python scripts/crawl_mard.py
```

### Bước 4: Xử lý documents

```bash
cd 09_chatbot
python scripts/process_documents.py
```

### Bước 5: Ingest vào ChromaDB

```bash
cd 09_chatbot
python scripts/ingest_to_chroma.py
```

### Bước 6: Test RAG pipeline

```bash
cd 02_backend
python -c "from app.services.rag_service import get_rag_service; s=get_rag_service(); print(s.chat('Cách nuôi gà thịt?'))"
```

### Bước 7: Khởi động Backend

```bash
cd 02_backend
python run.py
```

### Bước 8: Test API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Cách nuôi gà thịt?"}'
```

### Bước 9: Khởi động Frontend

```bash
cd 01_frontend
npm run dev
```

### Bước 10: Test trên web

Mở http://localhost:5173 → Dashboard → Chat

---

## Files cần tạo/sửa

| # | File | Mục đích |
|---|------|----------|
| 1 | `09_chatbot/scripts/crawl_mard.py` | Crawl dữ liệu từ mard.gov.vn |
| 2 | `09_chatbot/scripts/process_documents.py` | Parse HTML → Text chunks |
| 3 | `09_chatbot/scripts/ingest_to_chroma.py` | Embed + lưu vào ChromaDB |
| 4 | `02_backend/app/services/rag_service.py` | RAG Pipeline Service |
| 5 | `02_backend/app/api/chatbot.py` | Chat API endpoints |
| 6 | `02_backend/app/main.py` | Thêm chatbot router |
| 7 | `01_frontend/02_src/02_components/02.7_Chatbot/ChatBot.jsx` | Chat UI component |
| 8 | `01_frontend/02_src/02_components/02.7_Chatbot/ChatMessage.jsx` | Message component |
| 9 | `01_frontend/02_src/02_components/02.7_Chatbot/ChatInput.jsx` | Input component |
| 10 | `01_frontend/02_src/02_components/02.7_Chatbot/ChatBot.css` | Styling |
| 11 | `01_frontend/02_src/03_pages/Dashboard.jsx` | Thêm ChatBot |
| 12 | `09_chatbot/requirements.txt` | Dependencies |
| 13 | `02_backend/requirements.txt` | Thêm chromadb, sentence-transformers |
