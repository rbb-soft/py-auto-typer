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
        self.root.geometry("500x400")  # Ajustamos tamaño para el nuevo elemento
        
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
             
        self.btn_iniciar.config(state=tk.DISABLED)
        self.lbl_estado.config(text="¡Prepárate! Comenzando en 5 segundos...")
        
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
                # Mantén los mapeos anteriores que sí funcionaban
            }
            
            if char in key_map:
                # Modo de escritura especial para caracteres problemáticos
                keyboard.write(char, delay=0.03)
            else:
                # Método tradicional para el resto
                pyautogui.write(char)
                
            time.sleep(0.01)
            
        except Exception as e:
            logging.error(f"Error al escribir caracter: {char}", exc_info=True)
            raise

    def proceso_tipeo(self):
        try:
            logging.info("Iniciando proceso de tipeo automático")
            
            # Conteo regresivo
            for i in range(5, 0, -1):
                self.root.after(0, self.lbl_estado.config, {"text": f"Comenzando en {i}..."})
                time.sleep(1)
            
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
                time.sleep(1)
            
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