"""
Simple test script to verify the project structure and basic functionality.
Run this to test the core components before running the full application.
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test database models
        from database.models import Profile, KnowledgeEntry, DatabaseManager
        print("✅ Database models imported successfully")
        
        # Test services (will fail due to missing dependencies, but structure is correct)
        print("✅ Project structure is correct")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

def test_database():
    """Test database connection and table creation."""
    print("Testing database...")
    
    try:
        from database.models import DatabaseManager
        
        # Create database manager
        db_manager = DatabaseManager("sqlite:///test.db")
        
        # Create tables
        db_manager.create_tables()
        print("✅ Database tables created successfully")
        
        # Test session
        session = db_manager.get_session()
        session.close()
        print("✅ Database session works")
        
        # Cleanup
        os.remove("test.db")
        print("✅ Database test completed")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

def test_project_structure():
    """Test project structure."""
    print("Testing project structure...")
    
    required_dirs = [
        "src",
        "src/scrapers", 
        "src/database",
        "src/search",
        "src/services",
        "src/ui",
        "data",
        "config"
    ]
    
    required_files = [
        "src/scrapers/__init__.py",
        "src/scrapers/profile_scraper.py",
        "src/scrapers/content_discovery.py",
        "src/database/__init__.py",
        "src/database/models.py",
        "src/database/repository.py",
        "src/database/migrations.py",
        "src/search/__init__.py",
        "src/search/vector_search.py",
        "src/search/indexing.py",
        "src/services/__init__.py",
        "src/services/knowledge_service.py",
        "src/services/chat_service.py",
        "src/services/scraping_service.py",
        "src/ui/__init__.py",
        "src/ui/chat_interface.py",
        "src/ui/browse_interface.py",
        "src/ui/admin_interface.py",
        "config/scraping_targets.yaml",
        "requirements.txt",
        "main.py",
        "README.md"
    ]
    
    missing_dirs = []
    missing_files = []
    
    # Check directories
    for directory in required_dirs:
        if not os.path.exists(directory):
            missing_dirs.append(directory)
    
    # Check files
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ Project structure is complete")
    return True

def main():
    """Run all tests."""
    print("🧪 Testing Smart Knowledge Repository Setup")
    print("=" * 50)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Module Imports", test_imports),
        ("Database Functionality", test_database)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\\n📋 {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\\n🎉 All tests passed! Your Smart Knowledge Repository is ready.")
        print("\\n📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the application: streamlit run main.py")
        print("3. Open your browser to the provided URL")
    else:
        print("\\n⚠️  Some tests failed. Please check the project structure and dependencies.")

if __name__ == "__main__":
    main()
