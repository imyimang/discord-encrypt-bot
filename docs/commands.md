# 指令說明
* ###  **/help** 查看指令說明
* ### **/生成金鑰** 生成加密金鑰，如果已經有金鑰將會被覆蓋
* ### **/設定金鑰** 設定你的解密金鑰(解密他人檔案時可以用到)
* ### **/查詢金鑰** 查詢你當前的預設金鑰
* ### **/加密** 用金鑰加密你的檔案(檔案最大15MB)，如果還沒有金鑰會先生成一個，optional_key為選填，如果填寫本次就會用該金鑰解密，沒有填寫就會用預設金鑰解密，預設金鑰可以用**/查詢金鑰**來查詢
* ### **/解密** 用金鑰解密你的檔案(檔案最大15MB)，如果要解密其他金鑰加密的檔案請用**/設定金鑰**，optional_key為選填，如果填寫本次就會用該金鑰解密，沒有填寫就會用預設金鑰解密，預設金鑰可以用**/查詢金鑰**來查詢

