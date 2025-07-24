import json
import qrcode
import urllib.parse
import sys
import os
from typing import List, Dict

def generate_otpauth_url(token_data: Dict) -> str:
    """
    將 token 資料轉換成 otpauth:// URL 格式
    """
    # 獲取必要的參數
    secret = token_data.get('decrypted_seed', '')
    name = token_data.get('name', '')
    issuer = token_data.get('issuer', '')
    digits = token_data.get('digits', 6)
    
    # 如果沒有 issuer，嘗試從 name 中提取
    if not issuer and ':' in name:
        issuer = name.split(':')[0].strip()
    
    # 構建標籤（顯示名稱）
    if issuer and not name.startswith(issuer):
        label = f"{issuer}:{name}"
    else:
        label = name
    
    # URL 編碼
    label = urllib.parse.quote(label)
    
    # 構建 otpauth URL
    params = {
        'secret': secret,
        'digits': str(digits)
    }
    
    if issuer:
        params['issuer'] = issuer
    
    # 構建查詢字串
    query_string = urllib.parse.urlencode(params)
    
    # 完整的 otpauth URL
    otpauth_url = f"otpauth://totp/{label}?{query_string}"
    
    return otpauth_url

def generate_qr_code(otpauth_url: str, filename: str):
    """
    生成 QR code 圖片
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)

def convert_auth_tokens(json_file_path: str):
    """
    主函數：從檔案讀取並轉換認證令牌
    """
    try:
        # 讀取 JSON 檔案
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{json_file_path}'")
        return None
    except json.JSONDecodeError as e:
        print(f"錯誤：JSON 解析失敗 - {e}")
        return None
    except Exception as e:
        print(f"錯誤：讀取檔案時發生錯誤 - {e}")
        return None
    
    # 獲取 tokens
    tokens = data.get('decrypted_authenticator_tokens', [])
    
    if not tokens:
        print("警告：沒有找到任何 authenticator tokens")
        return []
    
    # 創建結果列表
    results = []
    
    print("=" * 60)
    print("Google Authenticator 匯入資訊")
    print("=" * 60)
    
    for i, token in enumerate(tokens, 1):
        # 生成 otpauth URL
        otpauth_url = generate_otpauth_url(token)
        
        # 儲存結果
        result = {
            'name': token.get('name', ''),
            'otpauth_url': otpauth_url,
            'qr_filename': f"qr_code_{i}_{token.get('unique_id', i)}.png"
        }
        results.append(result)
        
        # 顯示資訊
        print(f"\n帳號 {i}: {token.get('name', 'Unknown')}")
        print(f"Issuer: {token.get('issuer', 'N/A')}")
        print(f"Secret: {token.get('decrypted_seed', '')}")
        print(f"OTPAuth URL: {otpauth_url}")
        print(f"QR Code 檔案: {result['qr_filename']}")
        
        # 生成 QR code
        try:
            generate_qr_code(otpauth_url, result['qr_filename'])
            print(f"✓ QR Code 已生成")
        except Exception as e:
            print(f"✗ QR Code 生成失敗: {e}")
    
    # 儲存所有 URL 到文字檔
    with open('otpauth_urls.txt', 'w', encoding='utf-8') as f:
        f.write("Google Authenticator OTPAuth URLs\n")
        f.write("=" * 50 + "\n\n")
        for result in results:
            f.write(f"帳號: {result['name']}\n")
            f.write(f"URL: {result['otpauth_url']}\n")
            f.write("-" * 50 + "\n")
    
    print(f"\n✓ 已將所有 URL 儲存到 otpauth_urls.txt")
    print(f"✓ 共生成 {len(results)} 個 QR Code")
    
    return results

def main():
    """
    主程式進入點
    """
    # 檢查命令列參數
    if len(sys.argv) < 2:
        print("使用方法: python googleauth.py <json_file_path>")
        print("範例: python googleauth.py decrypted_tokens.json")
        sys.exit(1)
    
    # 獲取檔案路徑
    json_file_path = sys.argv[1]
    
    # 檢查檔案是否存在
    if not os.path.exists(json_file_path):
        print(f"錯誤：檔案 '{json_file_path}' 不存在")
        sys.exit(1)
    
    # 執行轉換
    results = convert_auth_tokens(json_file_path)
    
    if results is None:
        sys.exit(1)

if __name__ == "__main__":
    main()
