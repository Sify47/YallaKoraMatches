import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import os
import sys

def scrape_bayut_page(page_url):
    """دالة لجمع البيانات من صفحة واحدة"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"🌐 Fetching page: {page_url}")
        response = requests.get(page_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        print(f"✅ Page loaded successfully")
    except Exception as e:
        print(f"❌ Error loading page {page_url}: {e}")
        return []
    
    def text_or_none(selector, parent):
        el = parent.select_one(selector)
        return el.get_text(strip=True) if el else None
    
    property_cards = soup.select("ul._172b35d1 li")
    print(f"🔍 Found {len(property_cards)} property cards")
    
    properties = []
    
    for i, card in enumerate(property_cards[:10]):  # اختبار أول 10 فقط
        try:
            a = card.select_one("a._8969fafd")
            link = f"https://www.bayut.eg{a.get('href')}" if a and a.get('href') else None
            
            price = text_or_none("h4.afdad5da._71366de7 span.eff033a6", card) or text_or_none("span.eff033a6", card)
            title = text_or_none("h2._34c51035", card)
            
            spans = card.select("span._3002c6fb")
            type_ = spans[0].get_text(strip=True) if len(spans) > 0 else None
            bedrooms = spans[1].get_text(strip=True) if len(spans) > 1 else None
            bathrooms = spans[2].get_text(strip=True) if len(spans) > 2 else None
            
            location = text_or_none("h3._51c6b1ca", card)
            d = text_or_none("span.fd7ade6e", card)
            
            area_raw = text_or_none("h4._60820635._07b5f28e", card) or text_or_none("h4", card)
            area = area_raw[:-6] if area_raw and len(area_raw) > 6 else area_raw
            
            properties.append({
                'PropertyType': type_,
                'Link': link,
                'Title': title,
                'Price': price,
                'Location': location,
                'Area': area,
                'Bedrooms': bedrooms,
                'Bathrooms': bathrooms,
                'Down_Payment': d,
                'Scraped_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            print(f"  ✓ Property {i+1}: {title}")
            
        except Exception as e:
            print(f"  ✗ Error processing card {i+1}: {e}")
            continue
    
    return properties

def clean_scraped_data(df_clean):
    """دالة لتنظيف البيانات المجمعة"""
    print("🧹 Cleaning data...")
    try:
        df_temp = df_clean.copy()
        
        if not df_temp.empty:
            # تنظيف بسيط للبيانات
            if 'Price' in df_temp.columns:
                df_temp['Price'] = df_temp['Price'].astype(str).str.replace(',', '').str.replace('EGP', '').str.strip()
                df_temp['Price'] = pd.to_numeric(df_temp['Price'], errors='coerce')
            
            if 'Area' in df_temp.columns:
                df_temp['Area'] = df_temp['Area'].astype(str).str.replace('m²', '').str.strip()
                df_temp['Area'] = pd.to_numeric(df_temp['Area'], errors='coerce')
            
            if 'Bedrooms' in df_temp.columns:
                df_temp['Bedrooms'] = df_temp['Bedrooms'].astype(str).str.replace('studio', '1').str.strip()
                df_temp['Bedrooms'] = pd.to_numeric(df_temp['Bedrooms'], errors='coerce')
            
            # حساب Price_Per_M
            if 'Price' in df_temp.columns and 'Area' in df_temp.columns:
                df_temp['Price_Per_M'] = df_temp['Price'] / df_temp['Area']
                df_temp['Price_Per_M'] = df_temp['Price_Per_M'].round(2)
            
            # إضافة Payment_Method
            if 'Down_Payment' in df_temp.columns:
                df_temp['Payment_Method'] = "Cash"
                mask = df_temp['Down_Payment'].astype(str).str.contains(r'\d', na=False)
                df_temp.loc[mask, 'Payment_Method'] = "Installments"
        
        print(f"✅ Data cleaned. Final shape: {df_temp.shape}")
        return df_temp
        
    except Exception as e:
        print(f"❌ Error in cleaning data: {e}")
        return df_clean

def main():
    print("=" * 60)
    print("🚀 TEST: Starting real estate scraping...")
    print(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # جمع البيانات من صفحة واحدة فقط للاختبار
    base_url = "https://www.bayut.eg/en/alexandria/properties-for-sale/"
    
    print(f"📄 Testing with 1 page only...")
    properties = scrape_bayut_page(base_url)
    
    if properties:
        # تحويل إلى DataFrame
        df_scraped = pd.DataFrame(properties)
        print(f"\n📊 Collected {len(df_scraped)} test properties")
        
        # تنظيف البيانات
        df_cleaned = clean_scraped_data(df_scraped)
        
        if not df_cleaned.empty:
            # قراءة البيانات القديمة إذا وجدت
            if os.path.exists('Final1.csv'):
                try:
                    existing_df = pd.read_csv('Final1.csv')
                    print(f"📁 Found existing Final1.csv with {len(existing_df)} properties")
                    
                    # دمج البيانات
                    combined_df = pd.concat([existing_df, df_cleaned], ignore_index=True)
                    
                    # إزالة التكرارات البسيطة
                    combined_df = combined_df.drop_duplicates(subset=['Title', 'Location'], keep='last')
                    
                    new_properties = len(combined_df) - len(existing_df)
                    print(f"🔄 After merge: {len(combined_df)} total properties")
                    print(f"➕ New properties added: {new_properties}")
                    
                    # حفظ البيانات
                    combined_df.to_csv('Final1.csv', index=False, encoding='utf-8')
                    print(f"💾 Saved to Final1.csv")
                    
                except Exception as e:
                    print(f"⚠️ Error reading existing file: {e}")
                    df_cleaned.to_csv('Final1.csv', index=False, encoding='utf-8')
                    print(f"💾 Created new Final1.csv")
            else:
                # إذا لم يوجد الملف
                df_cleaned.to_csv('Final1.csv', index=False, encoding='utf-8')
                print(f"💾 Created Final1.csv with {len(df_cleaned)} properties")
            
            # حفظ metadata
            metadata = f"""Last scraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
New properties collected: {len(df_cleaned)}
Test mode: Single page
Success: Yes
Notes: Test scraping completed successfully"""
            
            with open('scraping_metadata.txt', 'w') as f:
                f.write(metadata)
            
            print("\n" + "=" * 60)
            print("✅ TEST COMPLETED SUCCESSFULLY!")
            print(f"📈 Summary:")
            print(f"   - Properties collected: {len(df_cleaned)}")
            print(f"   - File: Final1.csv")
            print(f"   - Metadata: scraping_metadata.txt")
            print("=" * 60)
            
            return True
        else:
            print("❌ No valid data after cleaning")
            return False
    else:
        print("❌ No properties collected")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
