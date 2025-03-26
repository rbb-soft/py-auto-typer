#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pyautogui
import threading
import time
import logging
import pygame.mixer  # Importamos pygame para manejo de sonido

class AutoTyperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoTipeador 5.0")
        self.root.geometry("650x600")
        self.input_mode = tk.StringVar(value="text")  # 'file' o 'text'
        self.file_path = None
        
        # Configuración logging
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
            self.typing_sound = pygame.mixer.Sound("key.mp3")  # Asegúrate de que click.wav esté en el mismo directorio
            self.typing_sound.set_volume(0.5)
        except Exception as e:
            logging.warning(f"No se pudo cargar el archivo de sonido: {str(e)}")
            self.typing_sound = None
        
        # Interfaz
        self.frame = tk.Frame(root, padx=20, pady=20)
        self.frame.pack(padx=10, pady=10)
        
        # Selector de modo
        self.mode_frame = tk.LabelFrame(self.frame, text="Modo de entrada", padx=10, pady=10,font=('Arial', 12))
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
                                       command=self.seleccionar_archivo, bg="#4CAF50", fg="white",font=('Arial', 12))
        self.btn_seleccionar.pack(pady=5)
        self.lbl_archivo = tk.Label(self.file_frame, text="Ningún archivo seleccionado", fg="#666",font=('Arial', 12))
        self.lbl_archivo.pack(pady=5)
        
        # Modo texto
        self.text_frame = tk.Frame(self.input_container)
        self.text_area = scrolledtext.ScrolledText(self.text_frame, wrap=tk.WORD, 
                                                  width=60, height=10)
        self.text_area.pack(padx=5, pady=5)
        self.text_area.bind("<KeyRelease>", self.check_text_input)
        self.text_area.bind("<ButtonRelease>", self.check_text_input)  # Detectar pegado con mouse
        
        # Opciones de tiempo
        self.frame_opciones = tk.Frame(self.frame)
        self.frame_opciones.pack(pady=15)
        vcmd = (self.root.register(self.validate_number), '%P')
        self.lbl_inicio = tk.Label(self.frame_opciones, text="Tiempo inicio (s):",font=('Arial', 12))
        self.lbl_inicio.grid(row=0, column=0, padx=5)
        self.entry_inicio = tk.Entry(self.frame_opciones, width=5, validate="key", validatecommand=vcmd)
        self.entry_inicio.insert(0, "5")
        self.entry_inicio.grid(row=0, column=1, padx=5)
        self.lbl_intervalo = tk.Label(self.frame_opciones, text="Retardo 'enter' (s):",font=('Arial', 12))
        self.lbl_intervalo.grid(row=0, column=2, padx=5)
        self.entry_intervalo = tk.Entry(self.frame_opciones, width=5, validate="key", validatecommand=vcmd)
        self.entry_intervalo.insert(0, "1.00")
        self.entry_intervalo.grid(row=0, column=3, padx=5)
        
        # Checkbox de sonido
        self.chk_sound = tk.Checkbutton(self.frame, text="Habilitar sonido de tecleo", 
                                       variable=self.sound_enabled, font=('Arial', 12))
        self.chk_sound.pack(pady=5)
        
        # Botón iniciar
        self.btn_iniciar = tk.Button(self.frame, text="Iniciar tipeo", 
                                   command=self.iniciar_tipeo, state=tk.DISABLED,
                                   bg="#2196F3", fg="black",font=('Arial', 12))
        self.btn_iniciar.pack(pady=20)
        
        # Checkbox logging
        self.log_var = tk.BooleanVar(value=False)
        self.chk_log = tk.Checkbutton(self.frame, text="Habilitar registro (log)", 
                                    variable=self.log_var, command=self.toggle_logging,font=('Arial', 12))
        self.chk_log.pack(pady=5)
        self.lbl_estado = tk.Label(self.frame, text="", fg="#009688")
        self.lbl_estado.pack()
        
        # Inicialización
        self.toggle_input_mode()
    
    def toggle_input_mode(self):
        mode = self.input_mode.get()
        # Ocultar todos
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
    
    def check_text_input(self, event=None):
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
            messagebox.showerror("Error", f"Error al seleccionar archivo:\n{str(e)}")
    
    def iniciar_tipeo(self):
        self.btn_iniciar.config(state=tk.DISABLED)
        self.lbl_estado.config(text=f"¡Prepárate! Comenzando en {self.entry_inicio.get()} segundos...")
        hilo = threading.Thread(target=self.proceso_tipeo)
        hilo.daemon = True
        hilo.start()
    
    def proceso_tipeo(self):
        try:
            # Obtener contenido
            if self.input_mode.get() == "file":
                if not self.file_path:
                    raise ValueError("Archivo no seleccionado")
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    contenido = f.read()
            else:
                contenido = self.text_area.get("1.0", tk.END).strip()
            lineas = contenido.splitlines()
            total_lineas = len(lineas)
            # Configuración tiempos
            start_delay = float(self.entry_inicio.get())
            action_interval = float(self.entry_intervalo.get())
            logging.info(f"Iniciando tipeo automático en {start_delay} segundos")
            time.sleep(start_delay)
            self.root.after(0, self.lbl_estado.config, {"text": "¡Escribiendo código... 👨💻"})
            for num_linea, linea in enumerate(lineas, 1):
                logging.debug(f"Escribiendo línea {num_linea}/{total_lineas}")
                for char in linea:
                    self.tipo_caracter_especial(char)
                    time.sleep(0.03)
                pyautogui.press('enter', interval=action_interval)
            logging.info("Tipeo finalizado exitosamente")
            self.root.after(0, self.lbl_estado.config, {"text": "¡Tipeo finalizado!"})
            self.root.after(2000, self.lbl_estado.config, {"text": ""})
            self.root.after(0, self.btn_iniciar.config, {"state": tk.NORMAL})
        except Exception as e:
            logging.error("Error durante el tipeo", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")
            self.restablecer()
    
    def tipo_caracter_especial(self, char):
        mapeo = {
            '<': (['shift'], ','),
            '!': (['shift'], '1'),
            '"': (['shift'], '2'),
            '$': (['shift'], '4'),
            '?': (['shift'], "/"),
            '_': (['shift'], '-')
        }
        try:
            if char in mapeo:
                modificadores, tecla = mapeo[char]
                # Presionar modificadores en orden
                for mod in modificadores:
                    pyautogui.keyDown(mod)
                    time.sleep(0.03)  # Delay necesario para registrar cada tecla
                # Presionar tecla principal
                self.play_sound()
                time.sleep(0.03)
                pyautogui.press(tecla)
                time.sleep(0.03)
                # Soltar modificadores en orden inverso
                for mod in reversed(modificadores):
                    pyautogui.keyUp(mod)
                    time.sleep(0.01)
            else:
                self.play_sound()
                pyautogui.write(char)
                time.sleep(0.03)
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
    
    def restablecer(self):
        self.root.after(0, self.lbl_estado.config, {"text": ""})
        self.root.after(0, self.btn_iniciar.config, {"state": tk.NORMAL})

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoTyperApp(root)
    root.mainloop()