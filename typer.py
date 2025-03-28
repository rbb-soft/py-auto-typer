#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pyautogui
import threading
import time
import logging
import pygame.mixer

class AutoTyperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoTipeador 5.0")
        self.root.geometry("650x720")
        
        # Variables de control
        self.input_mode = tk.StringVar(value="text")  # 'file' o 'text'
        self.file_path = None
        self.stop_flag = False  # Bandera para detener el proceso
        self.process_state = tk.StringVar(value="stopped")  # 'running', 'paused', 'resuming', 'stopped'
        self.pause_event = threading.Event()
        self.pause_event.set()  # Inicia sin pausa
        
        # Configuración de logging
        self.logger = logging.getLogger()
        self.log_handler = logging.FileHandler("autotyper.log")
        self.console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        self.console_handler.setFormatter(formatter)
        self.logger.addHandler(self.log_handler)
        self.logger.addHandler(self.console_handler)
        self.logger.setLevel(logging.INFO)
        
        # Inicialización de sonido
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.sound_enabled = tk.BooleanVar(value=True)
        try:
            self.typing_sound = pygame.mixer.Sound("key.mp3") 
            self.typing_sound.set_volume(0.5)  # Volumen inicial
        except Exception as e:
            logging.warning(f"No se pudo cargar el archivo de sonido: {str(e)}")
            self.typing_sound = None
        
        # Variables de configuración
        self.typing_speed = tk.DoubleVar(value=0.03)  # Velocidad en segundos por caracter
        self.volume_level = tk.DoubleVar(value=0.5)   # Nivel de volumen (0.0 - 1.0)
        
        # Interfaz gráfica
        self.frame = tk.Frame(root, padx=20, pady=20)
        self.frame.pack(padx=10, pady=10)
        
        # Selector de modo
        self.mode_frame = tk.LabelFrame(self.frame, text="Modo de entrada", padx=10, pady=10, font=('Arial', 12))
        self.mode_frame.pack(pady=10, fill="x")
        self.radio_file = tk.Radiobutton(self.mode_frame, text="Desde archivo", 
                                         variable=self.input_mode, value="file",
                                         command=self.toggle_input_mode)
        self.radio_file.grid(row=0, column=0, padx=10)
        self.radio_text = tk.Radiobutton(self.mode_frame, text="Texto manual", 
                                         variable=self.input_mode, value="text",
                                         command=self.toggle_input_mode)
        self.radio_text.grid(row=0, column=1, padx=10)
        
        # Contenedor de entrada
        self.input_container = tk.Frame(self.frame)
        self.input_container.pack(pady=10, fill="both", expand=True)
        
        # Modo archivo
        self.file_frame = tk.Frame(self.input_container)
        self.btn_seleccionar = tk.Button(self.file_frame, text="Seleccionar archivo", 
                                         command=self.seleccionar_archivo, bg="#4CAF50", fg="white", font=('Arial', 12))
        self.btn_seleccionar.pack(pady=5)
        self.lbl_archivo = tk.Label(self.file_frame, text="Ningún archivo seleccionado", fg="#666", font=('Arial', 12))
        self.lbl_archivo.pack(pady=5)
        
        # Modo texto
        self.text_frame = tk.Frame(self.input_container)
        self.button_frame = tk.Frame(self.text_frame)
        self.button_frame.pack(pady=5)
        self.btn_pegar = tk.Button(self.button_frame, text="📋 Portapapeles", 
                                   command=self.pegar_portapapeles, bg="#FFEB3B")
        self.btn_pegar.pack(side=tk.LEFT, padx=5)
        self.btn_limpiar = tk.Button(self.button_frame, text="🧹 Limpiar", 
                                     command=self.limpiar_texto, bg="#FF5722", fg="white")
        self.btn_limpiar.pack(side=tk.LEFT, padx=5)
        self.text_area = scrolledtext.ScrolledText(self.text_frame, wrap=tk.WORD, 
                                                  width=60, height=10)
        self.text_area.pack(padx=5, pady=5)
        self.text_area.bind("<KeyRelease>", self.check_text_validity)
        self.text_area.bind("<ButtonRelease>", self.check_text_validity)
        
        # Opciones avanzadas
        self.advanced_frame = tk.LabelFrame(self.frame, text="Configuración avanzada", padx=10, pady=10)
        self.advanced_frame.pack(pady=10, fill="x")
        
        # Tiempo inicio
        self.lbl_inicio = tk.Label(self.advanced_frame, text="Tiempo inicio (s):", font=('Arial', 12))
        self.lbl_inicio.grid(row=0, column=0, padx=5)
        vcmd = (self.root.register(self.validate_number), '%P')
        self.entry_inicio = tk.Entry(self.advanced_frame, width=5, validate="key", validatecommand=vcmd)
        self.entry_inicio.insert(0, "5")
        self.entry_inicio.grid(row=0, column=1, padx=5)
        
        # Retardo enter
        self.lbl_intervalo = tk.Label(self.advanced_frame, text="Retardo 'enter' (s):", font=('Arial', 12))
        self.lbl_intervalo.grid(row=0, column=2, padx=5)
        self.entry_intervalo = tk.Entry(self.advanced_frame, width=5, validate="key", validatecommand=vcmd)
        self.entry_intervalo.insert(0, "1.00")
        self.entry_intervalo.grid(row=0, column=3, padx=5)
        
        # Velocidad de tipeo
        self.lbl_speed = tk.Label(self.advanced_frame, text="Velocidad (s/tecla):", font=('Arial', 12))
        self.lbl_speed.grid(row=1, column=0, padx=5)
        self.scale_speed = tk.Scale(self.advanced_frame, from_=0.01, to=0.5, resolution=0.01,
                                   orient=tk.HORIZONTAL, variable=self.typing_speed)
        self.scale_speed.set(0.03)
        self.scale_speed.grid(row=1, column=1, columnspan=3, sticky='ew', padx=5)
        
        # Volumen
        self.lbl_volume = tk.Label(self.advanced_frame, text="Volumen:", font=('Arial', 12))
        self.lbl_volume.grid(row=2, column=0, padx=5)
        self.scale_volume = tk.Scale(self.advanced_frame, from_=0.0, to=1.0, resolution=0.05,
                                    orient=tk.HORIZONTAL, variable=self.volume_level,
                                    command=self.update_volume)
        self.scale_volume.set(0.5)
        self.scale_volume.grid(row=2, column=1, columnspan=3, sticky='ew', padx=5)
        
        # Checkbox de sonido
        self.chk_sound = tk.Checkbutton(self.frame, text="Habilitar sonido de tecleo", 
                                        variable=self.sound_enabled, font=('Arial', 12))
        self.chk_sound.pack(pady=5)
        
        # Botones iniciar, pausar y detener
        self.btn_frame = tk.Frame(self.frame)
        self.btn_frame.pack(pady=10)
        self.btn_iniciar = tk.Button(self.btn_frame, text="Iniciar tipeo", 
                                     command=self.iniciar_tipeo, state=tk.DISABLED,
                                     bg="#2196F3", fg="black", font=('Arial', 12))
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)
        self.btn_pausa = tk.Button(self.btn_frame, text="Pausar", 
                                   command=self.toggle_pausa, state=tk.DISABLED,
                                   bg="#FFA726", fg="black", font=('Arial', 12))
        self.btn_pausa.pack(side=tk.LEFT, padx=5)
        self.btn_detener = tk.Button(self.btn_frame, text="Detener", 
                                     command=self.detener_tipeo, state=tk.DISABLED,
                                     bg="#f44336", fg="white", font=('Arial', 12))
        self.btn_detener.pack(side=tk.LEFT, padx=5)
        
        # Cronómetro
        self.timer_label = tk.Label(self.frame, text="", fg="#009688", font=('Arial', 14, 'bold'))
        self.timer_label.pack(pady=10)
        
        # Checkbox logging
        self.log_var = tk.BooleanVar(value=False)
        self.chk_log = tk.Checkbutton(self.frame, text="Habilitar registro (log)", 
                                      variable=self.log_var, command=self.toggle_logging, font=('Arial', 12))
        self.chk_log.pack(pady=5)
        self.lbl_estado = tk.Label(self.frame, text="", fg="#009688")
        self.lbl_estado.pack()
        
        # Inicialización
        self.toggle_input_mode()

    def toggle_input_mode(self):
        mode = self.input_mode.get()
        self.file_frame.pack_forget()
        self.text_frame.pack_forget()
        if mode == "file":
            self.file_frame.pack(fill="x")
            self.text_area.config(state=tk.DISABLED)
            self.btn_seleccionar.config(state=tk.NORMAL)
        else:
            self.text_frame.pack(fill="both", expand=True)
            self.text_area.config(state=tk.NORMAL)
            self.btn_seleccionar.config(state=tk.DISABLED)
        self.check_input_validity()

    def check_text_validity(self, event=None):
        if self.input_mode.get() == "text":
            self.check_input_validity()

    def check_input_validity(self):
        valid = False
        if self.input_mode.get() == "file":
            valid = self.file_path is not None
        else:
            valid = len(self.text_area.get("1.0", tk.END).strip()) > 0
        self.btn_iniciar.config(state=tk.NORMAL if valid else tk.DISABLED)

    def validate_number(self, value):
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def toggle_logging(self):
        level = logging.INFO if self.log_var.get() else logging.CRITICAL
        self.logger.setLevel(level)
        self.log_handler.setLevel(level)
        self.console_handler.setLevel(level)
        logging.log(level, f"Registro {'habilitado' if level == logging.INFO else 'deshabilitado'}")

    def seleccionar_archivo(self):
        try:
            path = filedialog.askopenfilename()
            if path:
                self.file_path = path
                self.lbl_archivo.config(text=f"Archivo: {path}")
                self.check_input_validity()
            else:
                self.lbl_archivo.config(text="Ningún archivo seleccionado")
        except Exception as e:
            messagebox.showerror("Error", f"Error al seleccionar archivo: {str(e)}")

    def iniciar_tipeo(self):
        self.stop_flag = False
        self.process_state.set("running")
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_detener.config(state=tk.NORMAL)
        self.btn_pausa.config(state=tk.NORMAL)
        start_delay = float(self.entry_inicio.get())
        self.end_time = time.time() + start_delay
        self.lbl_estado.config(text=f"¡Prepárate! Comenzando en {start_delay} segundos...")
        self.update_countdown()

    def update_countdown(self):
        current_state = self.process_state.get()
        if current_state == "stopped":
            self.restablecer()
            return
            
        remaining = max(0, self.end_time - time.time())
        if remaining > 0:
            self.timer_label.config(text=f"Tiempo restante: {remaining:.1f} s")
            self.root.after(100, self.update_countdown)
        else:
            if current_state == "resuming":
                self.timer_label.config(text="¡Reanudando!")
                self.process_state.set("running")
                self.btn_pausa.config(text="Pausar", bg="#FFA726")
                self.lbl_estado.config(text="Escribiendo código... 💻", fg="#009688")
            else:
                self.timer_label.config(text="¡Comenzando!")
                hilo = threading.Thread(target=self.proceso_tipeo)
                hilo.daemon = True
                hilo.start()

    def toggle_pausa(self):
        if self.process_state.get() == "running":
            self.process_state.set("paused")
            self.pause_event.clear()
            self.btn_pausa.config(text="Continuar", bg="#4CAF50")
            self.lbl_estado.config(text="Proceso pausado ⏸", fg="#FFA726")
        elif self.process_state.get() == "paused":
            start_delay = float(self.entry_inicio.get())
            self.end_time = time.time() + start_delay
            self.process_state.set("resuming")
            self.pause_event.set()
            self.lbl_estado.config(text=f"¡Prepárate! Reanudando en {start_delay:.1f} segundos...")
            self.timer_label.config(text="")
            self.update_countdown()

    def detener_tipeo(self):
        self.process_state.set("stopped")
        self.pause_event.set()  # Libera cualquier pausa
        self.stop_flag = True
        self.timer_label.config(text="")
        self.lbl_estado.config(text="¡Proceso detenido!", fg="red")
        self.root.after(2000, lambda: self.lbl_estado.config(text=""))
        self.btn_detener.config(state=tk.DISABLED)
        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_pausa.config(state=tk.DISABLED, text="Pausar", bg="#FFA726")

    def proceso_tipeo(self):
        try:
            if self.input_mode.get() == "file":
                if not self.file_path:
                    raise ValueError("Archivo no seleccionado")
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    contenido = f.read()
            else:
                contenido = self.text_area.get("1.0", tk.END).strip()
            
            contenido = contenido.replace('    ', '\t')
            lineas = contenido.splitlines()
            total_lineas = len(lineas)
            
            action_interval = float(self.entry_intervalo.get())
            char_delay = self.typing_speed.get()
            logging.info(f"Iniciando tipeo automático con velocidad: {char_delay}s/tecla")
            
            self.root.after(0, self.lbl_estado.config, {"text": "¡Escribiendo código... 💻"})
            for num_linea, linea in enumerate(lineas, 1):
                while self.process_state.get() in ["paused", "resuming"]:
                    self.pause_event.wait()  # Espera activa
                    
                if self.process_state.get() == "stopped":
                    break
                
                logging.debug(f"Escribiendo línea {num_linea}/{total_lineas}")
                for char in linea:
                    while self.process_state.get() in ["paused", "resuming"]:
                        self.pause_event.wait()  # Pausa entre caracteres si es necesario
                        
                    if self.process_state.get() == "stopped":
                        break
                    
                    self.tipo_caracter_especial(char)
                    time.sleep(char_delay)
                
                if self.process_state.get() == "stopped":
                    break
                pyautogui.press('enter', interval=action_interval)
            
            logging.info("Tipeo finalizado exitosamente")
            self.root.after(0, self.lbl_estado.config, {"text": "¡Tipeo finalizado!"})
            self.root.after(2000, self.lbl_estado.config, {"text": ""})
            self.root.after(0, self.btn_iniciar.config, {"state": tk.NORMAL})
            self.root.after(0, self.btn_detener.config, {"state": tk.DISABLED})
            self.root.after(0, self.btn_pausa.config, {"state": tk.DISABLED, "text": "Pausar", "bg": "#FFA726"})
        except Exception as e:
            logging.error("Error durante el tipeo", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
            self.restablecer()

    def tipo_caracter_especial(self, char):
        mapeo = {
            '!': (['shift'], '1'),
            '"': (['shift'], '2'),
            '$': (['shift'], '4'),
            '?': (['shift'], "/"),
            '_': (['shift'], '-'),
            'á':([], 'a'),
            'é':([], 'e'),
            'í':([], 'i'),
            'ó':([], 'o'),
            'ú':([], 'u'),
            'ñ':([], 'n'),
            '#':(['shift'], '~')
        }
        try:
            if char in mapeo:
                modificadores, tecla = mapeo[char]
                for mod in modificadores:
                    pyautogui.keyDown(mod)
                    time.sleep(0.01)
                self.play_sound()
                time.sleep(0.01)
                pyautogui.press(tecla)
                time.sleep(0.01)
                for mod in reversed(modificadores):
                    pyautogui.keyUp(mod)
                    time.sleep(0.01)
            else:
                self.play_sound()
                pyautogui.write(char)
                time.sleep(0.01)
        except Exception as e:
            logging.error(f"Error al escribir caracter: {char}", exc_info=True)
            raise

    def play_sound(self):
        """Reproduce el sonido si está habilitado"""
        if self.sound_enabled.get() and self.typing_sound:
            try:
                self.typing_sound.play()
            except Exception as e:
                logging.warning(f"Error al reproducir sonido: {str(e)}")

    def update_volume(self, value):
        """Actualiza el volumen del canal de sonido"""
        try:
            volume = self.volume_level.get()
            if self.typing_sound:
                self.typing_sound.set_volume(volume)
        except Exception as e:
            logging.warning(f"Error al ajustar volumen: {str(e)}")

    def restablecer(self):
        self.root.after(0, self.lbl_estado.config, {"text": ""})
        self.root.after(0, self.btn_iniciar.config, {"state": tk.NORMAL})
        self.root.after(0, self.btn_detener.config, {"state": tk.DISABLED})
        self.root.after(0, self.btn_pausa.config, {"state": tk.DISABLED, "text": "Pausar", "bg": "#FFA726"})
        self.process_state.set("stopped")
        self.pause_event.set()

    def pegar_portapapeles(self):
        try:
            clipboard_text = self.root.clipboard_get()
            self.text_area.insert(tk.INSERT, clipboard_text)
            self.check_input_validity()
        except tk.TclError:
            messagebox.showerror("Error", "No hay texto en el portapapeles")

    def limpiar_texto(self):
        self.text_area.delete("1.0", tk.END)
        self.check_input_validity()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoTyperApp(root)
    root.mainloop()