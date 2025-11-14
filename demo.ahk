#Requires AutoHotkey v2.0

; --- In the VM window ---
Click(1079, 500)
; Send("#{Up}")          ; hotkey('win','up')
; Sleep(1000)
Click(300, 800)
Click(1000, 444)

; --- Open Chrome ---
Send("#s")               ; hotkey('win', 's')
Sleep(200)
Send("chrome")
Sleep(1000)
Send("{Enter}")
Sleep(3000)
Click(520, 750)
Send("#{Up}")
Sleep(1000)

; --- Chrome settings (commented) ---
; Send("^l")
; Send("chrome://settings/content/location?search=pop")
; Send("{Tab}{Tab}{Down}")
; Send("^l")
; Send("chrome://settings/content/popups?search=pop")
; Send("{Tab}{Tab}{Up}")

; --- Install GoLess extension (commented) ---
; Send("^l")
; Send("https://chromewebstore.google.com/detail/goless-browser-automation/ghlmiigebgipgagnhlanjmmniefbfihl")
; Sleep(200)
; Send("{Tab 5}")
; Send("{Enter}")
; Sleep(6000)
; Send("{Left}")
; Send("{Enter}")
