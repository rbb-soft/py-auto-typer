#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox
import pyautogui
import keyboard  
import threading
import time
import logging

class AutoTyperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoTipeador PHP 5.0")
        self.root.geometry("600x450")  # Ajustamos tamaño para nuevos elementos
        
        self.file_path = None
        
        # Configuración inicial de logging
        self.logger = logging.getLogger()
        self.log_handler = logging.FileHandler("autotyper.log")
        self.console_handler = logging.StreamHandler()
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(self.formatter)
        self.console_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.log_handler)
        self.logger.addHandler(self.console_handler)
        self.logger.setLevel(logging.INFO)
        
        # Interfaz gráfica
        self.frame = tk.Frame(root, padx=20, pady=20)
        self.frame.pack(padx=10, pady=10)
        
        self.btn_seleccionar = tk.Button(self.frame, text="Seleccionar archivo", 
                                       command=self.seleccionar_archivo, bg="#4CAF50", fg="white")
        self.btn_seleccionar.pack(pady=10)
        
        self.lbl_archivo = tk.Label(self.frame, text="Ningún archivo seleccionado", 
                                  wraplength=400, fg="#666")
        self.lbl_archivo.pack(pady=5)
        
        # Nuevos campos para tiempo e intervalo
        self.frame_opciones = tk.Frame(self.frame)
        self.frame_opciones.pack(pady=15)
        
        vcmd = (self.root.register(self.validate_number), '%P')
        
        self.lbl_inicio = tk.Label(self.frame_opciones, text="Tiempo inicio (s):", fg="#333", font=("Arial", 10, "bold"))
        self.lbl_inicio.grid(row=0, column=0, padx=5)
        self.entry_inicio = tk.Entry(self.frame_opciones, width=5, validate="key", validatecommand=vcmd)
        self.entry_inicio.insert(0, "5")
        self.entry_inicio.grid(row=0, column=1, padx=5)
        
        self.lbl_intervalo = tk.Label(self.frame_opciones, text="Intervalo (s):", fg="#333", font=("Arial", 10, "bold"))
        self.lbl_intervalo.grid(row=0, column=2, padx=5)
        self.entry_intervalo = tk.Entry(self.frame_opciones, width=5, validate="key", validatecommand=vcmd)
        self.entry_intervalo.insert(0, "0.03")
        self.entry_intervalo.grid(row=0, column=3, padx=5)
        
        self.btn_iniciar = tk.Button(self.frame, text="Iniciar tipeo", 
                                   command=self.iniciar_tipeo, state=tk.DISABLED,
                                   bg="#2196F3", fg="white")
        self.btn_iniciar.pack(pady=20)
        
        # Checkbox para habilitar/deshabilitar log
        self.log_var = tk.BooleanVar(value=False)
        self.chk_log = tk.Checkbutton(self.frame, text="Habilitar registro (log)", 
                                    variable=self.log_var, command=self.toggle_logging,
                                    fg="#009688")
        self.chk_log.pack(pady=5)
        
        self.lbl_estado = tk.Label(self.frame, text="", fg="#009688")
        self.lbl_estado.pack()

    def validate_number(self, value):
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def toggle_logging(self):
        """Habilita o deshabilita el registro según el estado del checkbox"""
        if self.log_var.get():
            self.logger.setLevel(logging.INFO)
            self.log_handler.setLevel(logging.INFO)
            self.console_handler.setLevel(logging.INFO)
            logging.info("Registro habilitado")
        else:
            self.logger.setLevel(logging.CRITICAL)
            self.log_handler.setLevel(logging.CRITICAL)
            self.console_handler.setLevel(logging.CRITICAL)
            logging.critical("Registro deshabilitado")

    def seleccionar_archivo(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("Archivos", "*.*")])
            if path:
                self.file_path = path
                logging.info(f"Archivo seleccionado: {path}")
                self.lbl_archivo.config(text=f"Archivo: {path}")
                self.btn_iniciar.config(state=tk.NORMAL)
            else:
                logging.warning("Selección cancelada por usuario")
                messagebox.showwarning("Advertencia", "No se seleccionó archivo")
        except Exception as e:
            logging.error("Error al seleccionar archivo", exc_info=True)
            messagebox.showerror("Error", f"Error al seleccionar archivo:\n{str(e)}")

    def iniciar_tipeo(self):
        if not self.file_path:
            error = "Primero selecciona un archivo válido"
            logging.error(error)
            messagebox.showerror("Error", error)
            return 
            
        try:
            self.start_delay = float(self.entry_inicio.get())
            self.action_interval = float(self.entry_intervalo.get())
        except ValueError:
            messagebox.showerror("Error", "Por favor ingresa números válidos en las opciones de tiempo")
            return
        
        self.btn_iniciar.config(state=tk.DISABLED)
        self.lbl_estado.config(text=f"¡Prepárate! Comenzando en {self.start_delay} segundos...")
        
        hilo = threading.Thread(target=self.proceso_tipeo)
        hilo.daemon = True
        hilo.start()
    
    def tipo_caracter_especial(self, char):
        try:
            # Mapeo universal usando códigos de teclado
            key_map = {
                '{': 'shift+[',
                '}': 'shift+]',
                '[': '[',
                ']': ']',
                '<': 'shift+,',
                '>': 'shift+.',
            }
            
            if char in key_map:
                keyboard.write(char, delay=0.03)
            else:
                pyautogui.write(char)
                
            time.sleep(self.action_interval)
            
        except Exception as e:
            logging.error(f"Error al escribir caracter: {char}", exc_info=True)
            raise

    def proceso_tipeo(self):
        try:
            logging.info("Iniciando proceso de tipeo automático")
            
            # Conteo regresivo
            start_time = time.time()
            while time.time() - start_time < self.start_delay:
                remaining = self.start_delay - (time.time() - start_time)
                self.root.after(0, self.lbl_estado.config, {"text": f"Comenzando en {remaining:.1f} segundos..."})
                time.sleep(0.1)
            
            # Leer archivo
            with open(self.file_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Preparar contenido para escritura
            lineas = contenido.splitlines()
            total_lineas = len(lineas)
            
            self.root.after(0, self.lbl_estado.config, {"text": "¡Escribiendo código... 👨💻"})
            logging.info(f"Iniciando escritura de {total_lineas} líneas")
            
            for num_linea, linea in enumerate(lineas, 1):
                logging.debug(f"Escribiendo línea {num_linea}/{total_lineas}")
                for char in linea:
                    self.tipo_caracter_especial(char)
                pyautogui.press('enter')
                time.sleep(self.action_interval)
            
            # Finalizar
            logging.info("Tipeo finalizado exitosamente")
            self.root.after(0, self.lbl_estado.config, {"text": "¡Tipeo finalizado!"})
            self.root.after(2000, self.lbl_estado.config, {"text": ""})
            self.root.after(0, self.btn_iniciar.config, {"state": tk.NORMAL})
            
        except Exception as e:
            logging.error("Error durante el tipeo", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")
            self.restablecer()

    def restablecer(self):
        self.root.after(0, self.lbl_estado.config, {"text": ""})
        self.root.after(0, self.btn_iniciar.config, {"state": tk.NORMAL})

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoTyperApp(root)
    root.mainloop()