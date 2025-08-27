# Smart Knowledge Repository

An intelligent knowledge management system that demonstrates advanced data collection, storage optimization, intelligent retrieval, and scope-aware AI interactions.

## Features

- **Intelligent Web Scraping**: Automatically discovers and extracts profile information from websites
- **Vector Search**: Semantic search capabilities using embeddings for intelligent content retrieval
- **Scope-Aware AI**: Context-limited AI responses with knowledge boundaries
- **Multi-Modal UI**: Streamlit-based interface with chat, browse, and admin functionalities
- **Database Management**: Professional SQLite database with full-text search capabilities

## Project Structure

```
smart_knowledge_repo/
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── profile_scraper.py
│   │   └── content_discovery.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── migrations.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── vector_search.py
│   │   └── indexing.py
│   ├── services/
│   │   ├── knowledge_service.py
│   │   ├── chat_service.py
│   │   └── scraping_service.py
│   └── ui/
│       ├── chat_interface.py
│       ├── browse_interface.py
│       └── admin_interface.py
├── data/
│   ├── profiles.db
│   └── embeddings/
├── config/
│   └── scraping_targets.yaml
├── requirements.txt
├── main.py
└── README.md
```

## Installation

1. Clone or download the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```python
python -c "from src.database.models import db_manager; db_manager.create_tables()"
```

## Usage

### Running the Application

Start the Streamlit application:
```bash
streamlit run main.py
```

### Using the Chat Interface

1. Navigate to the Chat tab
2. Ask questions about team members, roles, or departments
3. Use quick action buttons for common queries
4. Provide feedback on responses to improve the system

### Browsing the Knowledge Repository

1. Use the Browse tab to explore profiles and departments
2. Filter by department or role
3. Search for specific content using the advanced search

### Administrative Functions

1. Access the Admin tab (password: admin123)
2. Monitor system statistics and performance
3. Manage scraping jobs and data
4. Configure system settings

## Key Components

### Web Scraping
- **ProfileScraper**: Extracts structured profile information from web pages
- **ContentDiscovery**: Intelligently discovers relevant content sources

### Database Management
- **Models**: SQLAlchemy models for profiles, knowledge entries, and search indexes
- **Repository**: Clean data access patterns with CRUD operations
- **Migrations**: Database schema management and updates

### Search System
- **VectorSearch**: Semantic similarity search using embeddings
- **SemanticSearchEngine**: Combined vector and keyword search
- **ContentIndexer**: Maintains search indexes and embeddings

### Services
- **KnowledgeService**: High-level knowledge management operations
- **ChatService**: Conversational AI with scope awareness
- **ScrapingService**: Orchestrates web scraping tasks

### User Interface
- **ChatInterface**: Interactive chat with AI assistant
- **BrowseInterface**: Structured browsing of knowledge repository
- **AdminInterface**: System administration and monitoring

## Configuration

Edit `config/scraping_targets.yaml` to configure:
- Scraping targets and priorities
- Rate limiting and retry settings
- Search parameters
- Database connection
- UI preferences

## Core Requirements Met

✅ **Targeted Web Scraping**: Scrapes leadership team pages and extracts structured data
✅ **Local SQLite Database**: Stores profiles with full-text search capabilities
✅ **Streamlit Application**: Complete UI with chat and browse functionality
✅ **Rule-Based Scope Detection**: Checks query relevance before processing
✅ **Keyword-Based Search**: Implements efficient keyword retrieval
✅ **Data Categorization**: Organizes data by role and department

## Advanced Features

- **Vector Embeddings**: Semantic search using text embeddings
- **Hybrid Search**: Combines keyword and semantic search
- **Content Discovery**: Automatically finds new content sources
- **Search Analytics**: Tracks query performance and user feedback
- **Background Processing**: Asynchronous scraping operations
- **Data Export**: Export functionality for knowledge base content

## Development Notes

This implementation uses placeholder embeddings for demonstration. In production:
- Replace with actual embedding models (sentence-transformers, OpenAI embeddings)
- Implement proper authentication and authorization
- Add comprehensive error handling and logging
- Use proper task queues for background processing
- Implement data validation and sanitization

## Dependencies

- **streamlit**: Web UI framework
- **sqlalchemy**: Database ORM
- **beautifulsoup4**: HTML parsing
- **aiohttp**: Async HTTP client
- **scikit-learn**: TF-IDF vectorization
- **numpy**: Numerical computations
- **pandas**: Data manipulation
- **pyyaml**: Configuration file parsing

## License

This project is for educational and demonstration purposes.
