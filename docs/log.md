- ## 2024/5/22
    - 新增加解密指定金鑰功能

    - 更改加解密後檔案發送位置(dm --> slash response)

- ## 2024/5/23
    - 修復了在沒有設定金鑰時直接用金鑰解密時會發生錯誤的bug

    - 移除多餘的f.close()

- ## 2024/5/24
    - 新增temporary資料夾來暫存檔案，解決機器人檔案被誤刪的問題

    - 修復了keys或temporary資料夾被刪除時會導致機器人報錯的問題

    - 修復了加解密失敗後刪除檔案時報錯的問題

    - 修復了使用錯誤解密金鑰時錯誤訊息無法顯示的問題

    - 修復了輸入無效金鑰仍然能夠設定的問題

- ## 2024/5/25
    - 刪除了加解密檔案前要先下載檔案的過程，提升運行效率