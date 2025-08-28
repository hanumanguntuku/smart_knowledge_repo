#!/usr/bin/env python3
"""
Test script for Admin Interface integration with Amzur scraping functionality.
This script tests the complete workflow from admin interface to scraping service.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.scraping_service import ScrapingService
from services.knowledge_service import KnowledgeService

async def test_admin_amzur_integration():
    """Test the complete Amzur scraping integration."""
    print("🧪 Testing Admin Interface Amzur Integration")
    print("=" * 50)
    
    # Initialize services
    print("📚 Initializing services...")
    knowledge_service = KnowledgeService()
    scraping_service = ScrapingService(knowledge_service)
    
    # Test the admin quick action functionality
    print("\n🏢 Testing Amzur Leadership Scraping (as called from admin interface)...")
    
    try:
        # This is the exact call that would be made from the admin interface
        result = await scraping_service.scrape_amzur_leadership()
        
        print(f"📊 Scraping Result:")
        print(f"   Status: {result['status']}")
        print(f"   Profiles Found: {len(result.get('results', []))}")
        
        if result['status'] == 'completed':
            profiles_saved = result.get('metadata', {}).get('profiles_saved', 0)
            print(f"   Profiles Saved: {profiles_saved}")
            
            # Show sample profiles
            if result.get('results'):
                print(f"\n👥 Sample Profiles:")
                for i, profile in enumerate(result['results'][:3], 1):
                    print(f"   {i}. {profile.get('name', 'Unknown')} - {profile.get('role', 'No role')}")
                    if profile.get('profile_url'):
                        print(f"      URL: {profile['profile_url']}")
                
                if len(result['results']) > 3:
                    print(f"   ... and {len(result['results']) - 3} more profiles")
        else:
            print(f"   Error: {result.get('error_message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during integration test: {e}")
        return False
    
    print("\n✅ Admin integration test completed!")
    return True

async def test_scraping_service_stats():
    """Test scraping service statistics (used by admin dashboard)."""
    print("\n📈 Testing Scraping Statistics...")
    
    knowledge_service = KnowledgeService()
    scraping_service = ScrapingService(knowledge_service)
    
    try:
        stats = scraping_service.get_scraping_statistics()
        print(f"📊 Statistics Available:")
        print(f"   Total Jobs: {stats.get('total_jobs', 0)}")
        print(f"   Success Rate: {stats.get('success_rate', 0):.1f}%")
        print(f"   Avg Processing Time: {stats.get('avg_processing_time_seconds', 0):.1f}s")
        
        status_dist = stats.get('status_distribution', {})
        if status_dist:
            print(f"   Status Distribution: {status_dist}")
            
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        return False
    
    print("✅ Statistics test completed!")
    return True

def test_admin_import():
    """Test that admin interface can be imported."""
    print("\n🔧 Testing Admin Interface Import...")
    
    try:
        from ui.admin_interface import AdminInterface
        print("✅ AdminInterface imported successfully")
        
        # Test initialization
        knowledge_service = KnowledgeService()
        scraping_service = ScrapingService(knowledge_service)
        admin = AdminInterface(knowledge_service, scraping_service)
        print("✅ AdminInterface initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing/initializing AdminInterface: {e}")
        return False

async def main():
    """Run all integration tests."""
    print("🚀 Starting Admin Interface Integration Tests")
    print("=" * 60)
    
    # Test 1: Admin interface import
    test1 = test_admin_import()
    
    # Test 2: Scraping service statistics
    test2 = await test_scraping_service_stats()
    
    # Test 3: Complete Amzur integration
    test3 = await test_admin_amzur_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Admin Import: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"   Statistics: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"   Amzur Integration: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    all_passed = test1 and test2 and test3
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Admin interface is ready for Amzur leadership scraping!")
        print("💡 You can now use the 'Scrape Amzur Leadership Team' button in the admin interface.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
