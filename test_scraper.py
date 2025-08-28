#!/usr/bin/env python3
"""
Test script for the enhanced ProfileScraper with real Amzur.com data.

This script tests the scraper's ability to:
1. Discover profile URLs from the leadership team page
2. Extract basic profile information from the main page
3. Extract detailed information from individual profile pages
4. Handle real-world data extraction patterns
"""

import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.profile_scraper import ProfileScraper


async def test_amzur_scraping():
    """Test scraping Amzur.com leadership team."""
    
    print("🚀 Testing Amzur.com Profile Scraper...")
    print("=" * 50)
    
    async with ProfileScraper() as scraper:
        
        # Test 1: Discover profile URLs
        print("\\n1. 🔍 Discovering profile URLs...")
        leadership_url = "https://amzur.com/leadership-team/"
        discovered_urls = await scraper.discover_profiles(leadership_url)
        
        print(f"   Found {len(discovered_urls)} profile URLs:")
        for i, url in enumerate(discovered_urls[:5], 1):  # Show first 5
            print(f"   {i}. {url}")
        if len(discovered_urls) > 5:
            print(f"   ... and {len(discovered_urls) - 5} more")
        
        # Test 2: Extract basic profiles from main page
        print("\\n2. 📄 Extracting basic profiles from leadership page...")
        basic_profiles = await scraper.scrape_amzur_leadership_team()
        
        print(f"   Extracted {len(basic_profiles)} basic profiles:")
        for profile in basic_profiles[:3]:  # Show first 3
            print(f"   • {profile.name}")
            if profile.role:
                print(f"     Role: {profile.role}")
            if profile.department:
                print(f"     Department: {profile.department}")
            print(f"     URL: {profile.url}")
            print()
        
        # Test 3: Extract detailed profile from individual page
        if basic_profiles:
            print("\\n3. 🔍 Testing detailed extraction from individual page...")
            test_profile = basic_profiles[0]  # Test with first profile
            print(f"   Testing with: {test_profile.name}")
            
            detailed_profile = await scraper.extract_profile(test_profile.url)
            
            if detailed_profile:
                print("   ✅ Detailed extraction successful!")
                print(f"   Name: {detailed_profile.name}")
                print(f"   Role: {detailed_profile.role}")
                print(f"   Department: {detailed_profile.department}")
                if detailed_profile.bio:
                    bio_preview = detailed_profile.bio[:100] + "..." if len(detailed_profile.bio) > 100 else detailed_profile.bio
                    print(f"   Bio: {bio_preview}")
                if detailed_profile.contact:
                    print(f"   Contact: {detailed_profile.contact}")
                if detailed_profile.photo_url:
                    print(f"   Photo: {detailed_profile.photo_url}")
            else:
                print("   ❌ Detailed extraction failed")
        
        # Test 4: Test enhanced profiles (basic + detailed)
        print("\\n4. 🚀 Testing enhanced profile extraction...")
        print("   This will take a moment as it scrapes individual pages...")
        
        # Use only first 3 profiles for testing to avoid overwhelming the server
        test_profiles = basic_profiles[:3]
        enhanced_profiles = await scraper.enhance_profiles_with_details(test_profiles)
        
        print(f"   Enhanced {len(enhanced_profiles)} profiles:")
        for profile in enhanced_profiles:
            print(f"\\n   👤 {profile.name}")
            print(f"      Role: {profile.role or 'Not found'}")
            print(f"      Department: {profile.department or 'Not found'}")
            if profile.bio:
                bio_preview = profile.bio[:150] + "..." if len(profile.bio) > 150 else profile.bio
                print(f"      Bio: {bio_preview}")
            if profile.contact:
                print(f"      Contact: {profile.contact}")
            print(f"      URL: {profile.url}")
    
    print("\\n" + "=" * 50)
    print("✅ Scraping test completed!")


async def test_individual_profile():
    """Test extracting a specific individual profile."""
    
    print("\\n🎯 Testing individual profile extraction...")
    print("=" * 50)
    
    # Test with Bala Nemani's profile
    test_url = "https://amzur.com/leadership/bala-nemani/"
    
    async with ProfileScraper() as scraper:
        profile = await scraper.extract_profile(test_url)
        
        if profile:
            print("✅ Individual profile extraction successful!")
            print(f"Name: {profile.name}")
            print(f"Role: {profile.role}")
            print(f"Department: {profile.department}")
            if profile.bio:
                print(f"Bio length: {len(profile.bio)} characters")
                print(f"Bio preview: {profile.bio[:200]}...")
            if profile.contact:
                print(f"Contact info: {profile.contact}")
            if profile.photo_url:
                print(f"Photo URL: {profile.photo_url}")
        else:
            print("❌ Individual profile extraction failed")


def main():
    """Run all tests."""
    print("🧪 Profile Scraper Test Suite")
    print("Testing real data extraction from Amzur.com")
    print("=" * 60)
    
    try:
        # Run the async tests
        asyncio.run(test_amzur_scraping())
        asyncio.run(test_individual_profile())
        
    except KeyboardInterrupt:
        print("\\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
