# Authy-iOS-MiTM
使用 mitmproxy 從 Authy iOS 應用程式中提取認證器代碼的指南

## 要求
- 一部電腦 (Windows/Mac/Linux)

- 一部 iOS/iPadOS 裝置 (建議使用備用裝置)

- 對命令列和執行 Python 腳本有基本了解

## 步驟 1：設定 mitmproxy
提取代碼的原理是擷取 Authy 應用程式登入後收到的 HTTPS 流量。這些流量包含加密形式的代碼，稍後會進行解密，以便您存取您的認證器種子。為了接收這些流量，我們使用 mitmproxy，這是一個易於使用的工具，可讓您攔截裝置上應用程式和網站的流量。

首先，在您的電腦上安裝 [mitmproxy](https://www.mitmproxy.org)，然後在終端機中執行 `mitmweb --allow-hosts "api.authy.com"` 以啟動 mitmweb (這是 mitmproxy 的使用者友好介面)，並啟用 "api.authy.com" 的 HTTPS 代理。代理啟動後，前往「設定」->「Wi-Fi」->「(您的網路)」->「設定代理」，將其設定為「手動」，然後將您電腦的私有 IP 輸入「伺服器」，並將「連接埠」輸入 8080，以將您的 iOS 裝置連接到代理。

> [!NOTE]
> 您電腦的私有 IP 可以在其 Wi-Fi/網路設定中找到，通常格式為 "192.168.x.x" 或 "10.x.x.x"。

一旦您的 iOS 裝置連接到代理，您需要安裝 mitmproxy 根憑證頒發機構 (CA)，這是 HTTPS 代理所必需的。mitmproxy 使用的根 CA 金鑰是每次安裝隨機生成的，不會共享。要在您的 iOS 裝置上安裝根 CA，在代理連接狀態下，使用 Safari 瀏覽 `mitm.it`，然後點擊 iOS 部分下的「取得 mitmproxy-ca-cert.pem」。在 iOS 詢問是否安裝設定描述檔的訊息上點擊「允許」，然後前往「設定」，點擊「描述檔已下載」訊息，並確認安裝描述檔。**這可能看起來是結束了，但事實並非如此。** 憑證安裝後，您必須在「設定」->「一般」->「關於」->「憑證信任設定」中允許其根信任，才能使其在網站和應用程式上工作。未能執行此步驟將導致 Authy 出現 SSL 驗證錯誤。

至此，您已完成設定 mitmproxy 以擷取 iOS 裝置的 HTTPS 流量的過程。請保持代理連接以進行下一步，即轉儲從 Authy iOS 應用程式接收到的代碼。

## 步驟 2：轉儲代碼
> [!NOTE]
> 為了使其工作，您的 Authy 代碼必須同步到雲端，並且您必須設定備份密碼。建議使用備用裝置轉儲代碼，以防萬一。

> [!WARNING]
> 如果您只在單一裝置上使用 Authy，請務必在登出前[啟用 Authy 多裝置功能](https://help.twilio.com/articles/19753646900379-Enable-or-Disable-Authy-Multi-Device)。如果您沒有啟用，您將無法重新登入您的帳戶，並且必須等待 Twilio 在 24 小時後才能恢復您的帳戶。

轉儲代碼的第一步是從您的裝置上的 Authy 應用程式登出。不幸的是，Twilio 沒有在應用程式中實現「登出」功能，因此如果您已經登入，您必須從 App Store 刪除並重新安裝 Authy 應用程式。在代理連接狀態下，正常地重新登入應用程式 (輸入您的電話號碼，然後通過 SMS/電話/現有裝置進行驗證)，然後在應用程式詢問您的備份密碼時停止。

> [!NOTE]
> 如果您遇到「attestation token」(證明代碼) 錯誤，請嘗試在代理斷開連接的情況下打開 Authy 應用程式，輸入您的電話號碼，然後在點擊 SMS/電話/現有裝置驗證之前連接到代理。

此時，mitmproxy 應該已經以加密形式記錄了您的認證器代碼。要找到您的代碼，只需在 mitmweb UI 的「Flow List」選項卡中搜尋「authenticator_tokens」，然後查看每個顯示請求的「Response」，直到您看到類似這樣的內容：

````
{ "authenticator_tokens": [ { "account_type": "example", "digits": 6, "encrypted_seed": "something", "issuer": "Example.com", "key_derivation_iterations": 100000, "logo": "example", "name": "Example.com", "original_name": "Example.com", "password_timestamp": 12345678, "salt": "something", "unique_id": "123456", "unique_iv": null }, ...
````

顯然，您的將顯示您 Authy 帳戶中每個代碼的真實資訊。找到此請求後，切換到 mitmweb 中的「Flow」選項卡，然後點擊「Download」將此數據下載到一個名為「authenticator_tokens」的檔案中。將此檔案重新命名為「authenticator_tokens.json」，並在從電腦上的代理中退出 (在運行 mitmweb 的終端機視窗上按 Ctrl+C) 並繼續下一步之前，斷開您的裝置與代理的連接 (在「設定」->「Wi-Fi」->「(您的網路)」->「設定代理」中選擇「關閉」)。

## 步驟 3：解密代碼
您現在有一個包含您的代碼的 authenticator_tokens.json 檔案，但它是加密的，無法使用。幸運的是，這個檔案可以使用您的備份密碼和一個 Python 腳本來解密。下載此倉庫中的「decrypt.py」檔案，確保您的 authenticator_tokens.json 檔案與 decrypt.py 在同一個資料夾中，然後執行 `python3 decrypt.py` 來運行 Python 腳本。

> [!NOTE]
> 如果您收到找不到 python3 的錯誤，請從 [python.org](https://www.python.org) 在您的電腦上安裝 Python。如果您收到找不到 "cryptography" 套件的錯誤，請使用 `pip3 install cryptography` 安裝它。

腳本會提示您輸入備份密碼，出於隱私原因，密碼不會在終端機中顯示。輸入密碼並按下 Enter 後，您應該會得到一個 decrypted_tokens.json 檔案，其中包含從您的 Authy 帳戶解密出來的認證器種子。請注意，這個 JSON 檔案不是您可以匯入其他認證器應用程式的標準格式，但是有些人已經製作了腳本，將 decrypted_tokens.json 檔案轉換為其他認證器應用程式可識別的格式。我會在下面附上其中一些連結。

在終端機輸入以下程式碼，會立即整理並產生所有可以掃描的 QR CODE 可以使用 Google、Microsoft Auth 驗證器掃描並加入

```
pip install qrcode
python googleauth.py decrypted_tokens.json
```


> [!NOTE]
> 如果您在 JSON 檔案中看到 "Decryption failed: Invalid padding length" (解密失敗：無效填充長度) 作為 decrypted_seed，則表示您輸入了不正確的備份密碼。請使用正確的備份密碼再次運行腳本。

## 相容性說明
此方法永遠無法在未經 Root 的 Android 裝置上工作，因為 Authy 應用程式只信任系統儲存中的根憑證，並且需要 Root 才能將憑證新增到系統儲存中。如果您有 Root 的 Android 裝置並希望使用本指南，請改將 mitmproxy 憑證新增到系統儲存中，您應該就能正常地遵循本指南。此方法在 iOS 上之所以有效，是因為 iOS 預設將系統根 CA 和使用者安裝的根 CA 視為相同，除非應用程式使用 SSL pinning 或其他方法拒絕使用者安裝的根 CA，否則可以通過 MiTM 攻擊進行 HTTPS 攔截，而無需越獄。如果 Twilio 想要通過實施 SSL pinning 來修復此問題，他們絕對可以。

## 其他資訊
您可以在此 GitHub Gist 的評論中找到更多資訊：[https://gist.github.com/gboudreau/94bb0c11a6209c82418d01a59d958c93](https://gist.github.com/gboudreau/94bb0c11a6209c82418d01a59d958c93)。

如果在遵循本指南時出現問題，請提交 GitHub Issue，我會調查。
