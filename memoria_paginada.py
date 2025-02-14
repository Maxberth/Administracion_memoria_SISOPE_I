import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as patches
import random


class Proceso:
    def __init__(self, id_proceso, tamano, tiempo_llegada=0, tiempo_vida=None):
        self.id_proceso = id_proceso
        self.tamano = tamano
        self.tiempo_llegada = tiempo_llegada
        self.tiempo_vida = tiempo_vida
        self.paginas = []

    def __str__(self):
        return f"Proceso {self.id_proceso} (Tamaño: {self.tamano})"


class Memoria:
    def __init__(self, tamano_total, tamano_pagina):
        self.tamano_total = tamano_total
        self.tamano_pagina = tamano_pagina
        self.num_paginas = tamano_total // tamano_pagina
        self.memoria_fisica = [None] * self.num_paginas
        self.tabla_paginas = {}
        self.historial_asignaciones = []
        self.tiempo_actual = 0

    def asignar_memoria(self, proceso):
        num_paginas_necesarias = (proceso.tamano + self.tamano_pagina - 1) // self.tamano_pagina
        paginas_libres = [i for i, pagina in enumerate(self.memoria_fisica) if pagina is None]

        if len(paginas_libres) < num_paginas_necesarias:
            return False, 0

        paginas_asignadas = []
        for _ in range(num_paginas_necesarias):
            pagina_libre = paginas_libres.pop(0)
            self.memoria_fisica[pagina_libre] = proceso.id_proceso
            paginas_asignadas.append(pagina_libre)

        self.tabla_paginas[proceso.id_proceso] = paginas_asignadas
        proceso.paginas = paginas_asignadas
        self.historial_asignaciones.append((self.tiempo_actual, proceso.id_proceso, paginas_asignadas, []))
        return True, num_paginas_necesarias

    def desasignar_memoria(self, proceso):
        if proceso.id_proceso not in self.tabla_paginas:
            return 0

        paginas_liberadas = []
        for num_pagina in self.tabla_paginas[proceso.id_proceso]:
            self.memoria_fisica[num_pagina] = None
            paginas_liberadas.append(num_pagina)

        del self.tabla_paginas[proceso.id_proceso]
        self.historial_asignaciones.append((self.tiempo_actual, proceso.id_proceso, [], paginas_liberadas))
        proceso.paginas = []
        return len(paginas_liberadas)

    def generar_color_proceso(self, proceso_id):
        random.seed(proceso_id)
        r = random.randint(100, 255)
        g = random.randint(100, 255)
        b = random.randint(100, 255)
        return f'#{r:02x}{g:02x}{b:02x}'

    def obtener_info_paginas(self):
        info = []
        for i, proceso_id in enumerate(self.memoria_fisica):
            if proceso_id is not None:
                info.append(f"Página {i}: Proceso {proceso_id}")
            else:
                info.append(f"Página {i}: Libre")
        return info

    def reiniciar_memoria(self, nuevo_tamano_total):
        self.tamano_total = nuevo_tamano_total
        self.num_paginas = self.tamano_total // self.tamano_pagina
        self.memoria_fisica = [None] * self.num_paginas
        self.tabla_paginas = {}
        self.historial_asignaciones = []
        self.tiempo_actual = 0



class SimulacionApp:
    def __init__(self, root):
        self.root = root
        root.title("Simulador de Memoria Paginada")
        # Usar dimensiones de la pantalla para maximizar
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.geometry(f"{width}x{height}")
        root.state('zoomed') # Iniciar maximizada

        # Valores iniciales
        self.tamano_memoria = 64
        self.tamano_pagina = 4
        self.memoria = Memoria(self.tamano_memoria, self.tamano_pagina)
        self.procesos_creados = []
        self.id_proceso_var = tk.IntVar()
        self.tamano_proceso_var = tk.IntVar()
        self.tiempo_vida_proceso_var = tk.IntVar()
        self.tamano_memoria_var = tk.IntVar(value=self.tamano_memoria)

        self.crear_interfaz()
        self.actualizar_visualizacion()

    def crear_interfaz(self):
        # --- Frames Principales ---
        frame_controles = ttk.Frame(self.root, padding=10)
        frame_controles.pack(side=tk.LEFT, fill=tk.Y)

        frame_visualizacion = ttk.Frame(self.root, padding=10)
        frame_visualizacion.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Controles (Frame Izquierdo) ---
        ttk.Label(frame_controles, text="Configuración de Memoria", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(frame_controles, text="Tamaño Total de Memoria (bytes):").pack()
        tamano_memoria_entry = ttk.Entry(frame_controles, textvariable=self.tamano_memoria_var)
        tamano_memoria_entry.pack()
        actualizar_memoria_btn = ttk.Button(frame_controles, text="Actualizar Memoria", command=self.actualizar_tamano_memoria)
        actualizar_memoria_btn.pack(pady=5)

        ttk.Label(frame_controles, text="Crear Proceso", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(frame_controles, text="ID del Proceso:").pack()
        id_entry = ttk.Entry(frame_controles, textvariable=self.id_proceso_var)
        id_entry.pack()
        ttk.Label(frame_controles, text="Tamaño del Proceso (bytes):").pack()
        tamano_entry = ttk.Entry(frame_controles, textvariable=self.tamano_proceso_var)
        tamano_entry.pack()
        ttk.Label(frame_controles, text="Tiempo de Vida (-1 para indefinido):").pack()
        vida_entry = ttk.Entry(frame_controles, textvariable=self.tiempo_vida_proceso_var)
        vida_entry.pack()
        crear_btn = ttk.Button(frame_controles, text="Crear Proceso", command=self.crear_proceso)
        crear_btn.pack(pady=5)

        ttk.Label(frame_controles, text="Eliminar Proceso", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(frame_controles, text="ID del Proceso a Eliminar:").pack()
        self.id_eliminar_var = tk.IntVar()
        id_eliminar_entry = ttk.Entry(frame_controles, textvariable=self.id_eliminar_var)
        id_eliminar_entry.pack()
        eliminar_btn = ttk.Button(frame_controles, text="Eliminar Proceso", command=self.eliminar_proceso)
        eliminar_btn.pack(pady=5)

        ttk.Label(frame_controles, text="Avanzar Tiempo", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(frame_controles, text="Pasos de Tiempo:").pack()
        self.pasos_tiempo_var = tk.IntVar(value=1)
        pasos_tiempo_entry = ttk.Entry(frame_controles, textvariable=self.pasos_tiempo_var)
        pasos_tiempo_entry.pack()
        avanzar_btn = ttk.Button(frame_controles, text="Avanzar Tiempo", command=self.avanzar_tiempo)
        avanzar_btn.pack(pady=5)

        ttk.Label(frame_controles, text="Historial de Asignaciones", font=("Arial", 12, "bold")).pack(pady=5)
        self.historial_text = scrolledtext.ScrolledText(frame_controles, width=40, height=10)
        self.historial_text.pack()

        ttk.Label(frame_controles, text="Información de Memoria", font=("Arial", 12, "bold")).pack(pady=5)
        self.info_memoria_label = ttk.Label(frame_controles, text=self.obtener_info_memoria())
        self.info_memoria_label.pack()


        # --- Visualización (Frame Derecho) - SOLO Memoria Física ---
        self.fig = Figure()  # Crear la figura
        self.ax1 = self.fig.add_subplot(1, 1, 1) # Un solo subplot que ocupa toda la figura

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_visualizacion)
        self.canvas_widget = self.canvas.get_tk_widget()  # Obtener el widget
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True) # expand=True!


    def actualizar_tamano_memoria(self):
        try:
            nuevo_tamano = self.tamano_memoria_var.get()
            if nuevo_tamano <= 0:
                messagebox.showerror("Error", "El tamaño de la memoria debe ser mayor que cero.")
                return
            if nuevo_tamano % self.tamano_pagina != 0:
                messagebox.showerror("Error", f"El tamaño de memoria deber ser multiplo del tamaño de pagina ({self.tamano_pagina})")
                return

            for proc in self.procesos_creados:
                self.memoria.desasignar_memoria(proc)
            self.procesos_creados = []

            self.memoria.reiniciar_memoria(nuevo_tamano)
            self.actualizar_historial()
            self.actualizar_visualizacion()
            messagebox.showinfo("Memoria Actualizada", f"Tamaño de memoria actualizado a {nuevo_tamano} bytes.")

        except ValueError:
            messagebox.showerror("Error", "Entrada no válida para el tamaño de memoria.")

    def crear_proceso(self):
        try:
            id_proceso = self.id_proceso_var.get()
            tamano = self.tamano_proceso_var.get()
            tiempo_vida = self.tiempo_vida_proceso_var.get()
            tiempo_vida = None if tiempo_vida == -1 else tiempo_vida

            if any(p.id_proceso == id_proceso for p in self.procesos_creados):
                messagebox.showerror("Error", "Ya existe un proceso con ese ID.")
                return

            nuevo_proceso = Proceso(id_proceso, tamano, self.memoria.tiempo_actual, tiempo_vida)
            asignado, num_paginas = self.memoria.asignar_memoria(nuevo_proceso)
            if asignado:
                self.procesos_creados.append(nuevo_proceso)
                messagebox.showinfo("Proceso Creado",
                                    f"Proceso {id_proceso} creado y asignado. Páginas asignadas: {num_paginas}")
                self.actualizar_historial()
                self.actualizar_visualizacion()
            else:
                messagebox.showerror("Error", "No hay suficiente memoria para el proceso.")

        except ValueError:
            messagebox.showerror("Error", "Entrada no válida. Asegúrate de introducir números.")

    def eliminar_proceso(self):
        try:
            id_eliminar = self.id_eliminar_var.get()
            proceso_a_eliminar = None

            for proc in self.procesos_creados:
                if proc.id_proceso == id_eliminar:
                    proceso_a_eliminar = proc
                    break

            if proceso_a_eliminar:
                paginas_liberadas = self.memoria.desasignar_memoria(proceso_a_eliminar)
                self.procesos_creados.remove(proceso_a_eliminar)
                messagebox.showinfo("Proceso Eliminado",
                                    f"Proceso {id_eliminar} eliminado. Páginas liberadas: {paginas_liberadas}")
                self.actualizar_historial()
                self.actualizar_visualizacion()
            else:
                messagebox.showerror("Error", "No se encontró un proceso con ese ID.")
        except ValueError:
             messagebox.showerror("Error", "Entrada no válida. Asegúrate de introducir un número.")

    def avanzar_tiempo(self):
        try:
            pasos = self.pasos_tiempo_var.get()
            for _ in range(pasos):
                self.memoria.tiempo_actual += 1
                procesos_a_eliminar = []
                for proc in self.procesos_creados:
                    if proc.tiempo_vida is not None and self.memoria.tiempo_actual >= proc.tiempo_llegada + proc.tiempo_vida:
                        procesos_a_eliminar.append(proc)
                for proc in procesos_a_eliminar:
                    self.memoria.desasignar_memoria(proc)
                    self.procesos_creados.remove(proc)
                    self.actualizar_historial()
                    print(f"Tiempo {self.memoria.tiempo_actual}: Proceso {proc.id_proceso} finalizado y liberado.")
            self.actualizar_visualizacion()

        except ValueError:
            messagebox.showerror("Error", "Entrada no válida para los pasos de tiempo.")

    def actualizar_historial(self):
        self.historial_text.delete("1.0", tk.END)
        for tiempo, proceso_id, paginas_asignadas, paginas_liberadas in self.memoria.historial_asignaciones:
            if paginas_asignadas:
                self.historial_text.insert(tk.END,
                                           f"Tiempo {tiempo}: Proceso {proceso_id} ASIGNADO - Páginas: {paginas_asignadas}\n")
            elif paginas_liberadas:
                self.historial_text.insert(tk.END,
                                           f"Tiempo {tiempo}: Proceso {proceso_id} LIBERADO - Páginas: {paginas_liberadas}\n")

    def actualizar_visualizacion(self):
        self.ax1.clear()  # Limpiar el subplot

        # --- Memoria Física (Ahora ocupa todo el espacio) ---
        self.ax1.set_title("Memoria Física (Paginada)")
        self.ax1.set_xlabel("Número de Página")
        self.ax1.set_ylabel("Estado")
        self.ax1.set_yticks([])
        self.ax1.set_xticks(range(self.memoria.num_paginas))
        self.ax1.set_xlim(-0.5, self.memoria.num_paginas - 0.5)
        self.ax1.set_ylim(-0.5, 0.5)
        self.ax1.set_aspect('equal')

        for i in range(self.memoria.num_paginas):
            color = 'lightgray'
            label = 'Libre'
            if self.memoria.memoria_fisica[i] is not None:
                proceso_id = self.memoria.memoria_fisica[i]
                color = self.memoria.generar_color_proceso(proceso_id)
                label = f'P{proceso_id}'

            rect = patches.Rectangle((i - 0.4, -0.4), 0.8, 0.8, linewidth=1, edgecolor='black', facecolor=color)
            self.ax1.add_patch(rect)
            self.ax1.text(i, 0, label, ha='center', va='center', color='black')

        self.canvas.draw()  # Redibujar el canvas
        self.info_memoria_label.config(text=self.obtener_info_memoria())  # Actualizar info
        self.root.update_idletasks() # Actualiza la interfaz.


    def obtener_info_memoria(self):
      return (f"Tamaño total de la memoria: {self.memoria.tamano_total} bytes\n"
              f"Tamaño de página: {self.memoria.tamano_pagina} bytes\n"
              f"Número total de páginas: {self.memoria.num_paginas}\n"
              f"Tiempo actual: {self.memoria.tiempo_actual}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SimulacionApp(root)
    root.mainloop()