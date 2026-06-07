"""
Quick test script to diagnose Chrome/ChromeDriver connection issues.
Run this to test if WebDriver can initialize properly.
"""
import sys
from driver_manager import DriverManager
from utils import setup_logger

logger = setup_logger(__name__)

def test_driver():
    print("=" * 60)
    print("Testing Chrome WebDriver Initialization")
    print("=" * 60)
    
    try:
        print("\n1️⃣ Creating DriverManager...")
        dm = DriverManager(headless=False)
        
        print("2️⃣ Attempting to get WebDriver...")
        driver = dm.get_driver()
        
        print("3️⃣ Testing navigation...")
        driver.get("https://www.google.com")
        print(f"   ✅ Successfully loaded: {driver.current_url}")
        print(f"   ✅ Page title: {driver.title}")
        
        print("\n4️⃣ Closing driver...")
        dm.close_driver()
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! WebDriver is working correctly.")
        print("=" * 60)
        print("\nYou can now run the full scraper:")
        print("   python scraper.py")
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ FAILED! WebDriver initialization error")
        print("=" * 60)
        print(f"\nError: {e}\n")
        
        print("🔍 Troubleshooting Steps:")
        print("\n1. CHECK CHROME BROWSER:")
        print("   • Is Google Chrome installed?")
        print("   • Open Chrome and check: chrome://version/")
        
        print("\n2. NETWORK ISSUES:")
        print("   • Are you behind a corporate proxy/firewall?")
        print("   • Can you access: https://chromedriver.storage.googleapis.com/")
        print("   • Try disconnecting from VPN if applicable")
        
        print("\n3. ANTIVIRUS/FIREWALL:")
        print("   • Temporarily disable antivirus")
        print("   • Check Windows Defender settings")
        print("   • Allow Python through Windows Firewall")
        
        print("\n4. MANUAL CHROMEDRIVER INSTALLATION:")
        print("   • Download ChromeDriver manually from:")
        print("     https://googlechromelabs.github.io/chrome-for-testing/")
        print("   • Extract chromedriver.exe to project folder")
        print("   • Update driver_manager.py to use local path")
        
        print("\n5. ALTERNATIVE: Use Firefox instead")
        print("   • Install Firefox browser")
        print("   • pip install selenium webdriver-manager")
        print("   • Modify driver_manager.py to use Firefox")
        
        return False

if __name__ == "__main__":
    success = test_driver()
    sys.exit(0 if success else 1)
