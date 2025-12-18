import time
import json
import keyboard
import pyperclip
from googletrans import Translator, LANGUAGES
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import plyer  # pip install plyer

class TranslatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Многоязычный Переводчик")
        self.root.geometry("600x550")
        
        self.translator = Translator()
        self.history = self.load_history()
        self.current_src = tk.StringVar(self.root, value='auto')
        self.current_dest = tk.StringVar(self.root, value='ru')
        
        self.setup_ui()
        self.setup_hotkeys()
        
    def notification(self, title, message, duration=5):
        try:
            plyer.notification.notify(
                title=title,
                message=message[:100],
                timeout=duration
            )
        except:
            print(f"[Уведомление] {title}: {message}")
    
    def safe_translate(self, text, src_lang='auto', dest_lang='ru'):
        """Тихий перевод БЕЗ print ошибок"""
        valid_langs = list(LANGUAGES.keys())
        
        # Нормализуем zh-cn → zh
        if src_lang == 'zh-cn': src_lang = 'zh'
        if dest_lang == 'zh-cn': dest_lang = 'zh'
        
        try:
            # 1. Пробуем с src
            if src_lang != 'auto':
                result = self.translator.translate(text, src=src_lang, dest=dest_lang)
                return result.text, result.src if result.src else src_lang
            
            # 2. Автоопределение
            result = self.translator.translate(text, dest=dest_lang)
            return result.text, result.src if result.src else 'auto'
            
        except:
            # 3. Fallback - только dest
            try:
                result = self.translator.translate(text, dest=dest_lang)
                return result.text, 'auto'
            except:
                return text, 'error'
    
    def setup_ui(self):
        lang_frame = ttk.Frame(self.root)
        lang_frame.pack(pady=10)
        
        ttk.Label(lang_frame, text="Из:").pack(side=tk.LEFT)
        self.src_combo = ttk.Combobox(lang_frame, textvariable=self.current_src, 
                                     values=['auto', 'ja', 'ru', 'en', 'de', 'zh', 'fr', 'es'], 
                                     width=10, state='readonly')
        self.src_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(lang_frame, text="→").pack(side=tk.LEFT, padx=(20,5))
        
        ttk.Label(lang_frame, text="В:").pack(side=tk.LEFT)
        self.dest_combo = ttk.Combobox(lang_frame, textvariable=self.current_dest, 
                                      values=['ru', 'ja', 'en', 'de', 'zh', 'fr', 'es'], 
                                      width=10, state='readonly')
        self.dest_combo.pack(side=tk.LEFT, padx=5)
        
        # Легенда (убрал zh-cn)
        legend_text = "auto:🚀 ja:🇯🇵 ru:🇷🇺 en:🇺🇸 de:🇩🇪 zh:🇨🇳 fr:🇫🇷 es:🇪🇸"
        ttk.Label(self.root, text=legend_text, font=('Arial', 8)).pack(pady=5)
        
        # Кнопки
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Перевод в уведомлении", 
                  command=self.translate_to_toast).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Заменить текст", 
                  command=self.translate_and_replace).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Автоопределение", 
                  command=self.auto_detect).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить историю", 
                  command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
        # История
        ttk.Label(self.root, text="История переводов:").pack(anchor=tk.W, padx=10)
        self.history_text = scrolledtext.ScrolledText(self.root, height=15, width=80)
        self.history_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.update_history_display()
        
    def save_history(self):
        with open('translation_history.json', 'w', encoding='utf-8') as f:
            json.dump(self.history[-100:], f, ensure_ascii=False, indent=2)
    
    def load_history(self):
        try:
            with open('translation_history.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def add_to_history(self, original, translated, detected='auto'):
        entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'src': self.current_src.get(),
            'dest': self.current_dest.get(),
            'detected': detected,
            'original': original,
            'translated': translated
        }
        self.history.append(entry)
        self.save_history()
        self.update_history_display()
    
    def update_history_display(self):
        self.history_text.delete(1.0, tk.END)
        for entry in reversed(self.history[-20:]):
            detected = f" [{entry.get('detected')}]" if entry.get('detected') != 'auto' else ""
            line = f"[{entry['time']}] {entry['src']}→{entry['dest']}: {entry['original'][:40]}{detected} → {entry['translated'][:40]}...\n"
            self.history_text.insert(tk.END, line)
    
    def clear_history(self):
        self.history = []
        self.save_history()
        self.update_history_display()
    
    def translate_to_toast(self):
        keyboard.press_and_release('ctrl+c')
        time.sleep(0.1)
        text = pyperclip.paste().strip()
        if not text:
            self.notification("Перевод", "Буфер пустой", 2)
            return
        
        translated, detected = self.safe_translate(text, self.current_src.get(), self.current_dest.get())
        self.notification(f"{detected} → {self.current_dest.get()}", translated, 5)
        self.add_to_history(text, translated, detected)
    
    def translate_and_replace(self):
        keyboard.press_and_release('ctrl+c')
        time.sleep(0.1)
        original = pyperclip.paste().strip()
        if not original:
            print("Буфер пуст")
            return
        
        translated, detected = self.safe_translate(original, self.current_src.get(), self.current_dest.get())
        pyperclip.copy(translated)
        time.sleep(0.05)
        keyboard.send('ctrl+v')
        self.add_to_history(original, translated, detected)
    
    def auto_detect(self):
        keyboard.press_and_release('ctrl+c')
        time.sleep(0.1)
        text = pyperclip.paste().strip()
        if not text:
            messagebox.showwarning("Автоопределение", "Буфер пустой")
            return
        
        _, detected = self.safe_translate(text)
        messagebox.showinfo("Автоопределение", f"Язык: {detected}\n\n{text[:100]}...")
        if detected not in ['error', 'unknown']:
            self.current_src.set(detected)
    
    def setup_hotkeys(self):
        keyboard.add_hotkey('shift+alt+e', self.translate_to_toast)
        keyboard.add_hotkey('shift+alt+q', self.translate_and_replace)
        keyboard.add_hotkey('shift+alt+r', self.root.quit)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TranslatorApp()
    print("Shift+Alt+E — перевод в уведомлении")
    print("Shift+Alt+Q — заменить текст") 
    print("Shift+Alt+R — выход")
    app.run()
