import customtkinter as ctk
from tkinter import messagebox, simpledialog, Toplevel, Listbox, END, ttk, Text
from PIL import Image
from fpdf import FPDF
import datetime
import time
import json
import os
import sys
# --- LIBRERÍAS DE CORREO ACTIVADAS ---
import smtplib
import socket # Para verificar la conexión
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- FUNCIÓN AÑADIDA PARA COMPATIBILIDAD CON .EXE ---
def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Configuración Inicial y Simulación de Base de Datos ---

DB_FILES = {
    "users": "users.json",
    "inventory": "inventory.json",
    "sales": "sales.json",
    "config": "config.json",
    "email": "email_config.json"
}

def setup_database():
    """Inicializa los archivos JSON si no existen."""
    if not os.path.exists(DB_FILES["users"]):
        admin_user = {"admin": {"password": "admin", "role": "administrador"}, "vendedor": {"password": "123", "role": "vendedor"}}
        with open(DB_FILES["users"], "w") as f: json.dump(admin_user, f, indent=4)
    if not os.path.exists(DB_FILES["inventory"]):
        sample_inventory = {"SKU001": {"name": "Camisa de Lino Blanca", "price": 450.0, "quantity": 20}, "SKU002": {"name": "Pantalón de Mezclilla Azul", "price": 750.0, "quantity": 15}}
        with open(DB_FILES["inventory"], "w") as f: json.dump(sample_inventory, f, indent=4)
    if not os.path.exists(DB_FILES["sales"]):
        with open(DB_FILES["sales"], "w") as f: json.dump([], f, indent=4)
    if not os.path.exists(DB_FILES["config"]):
        default_config = {"appearance_mode": "dark", "color_theme": "blue", "last_ticket_number": 0}
        with open(DB_FILES["config"], "w") as f: json.dump(default_config, f, indent=4)
    
    if not os.path.exists(DB_FILES["email"]):
        email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "boutiqueelimpulso@gmail.com",
            "sender_password": "ovzc bsby arce hrhu"
        }
        with open(DB_FILES["email"], "w") as f:
            json.dump(email_config, f, indent=4)

def read_db(file_key):
    with open(DB_FILES[file_key], "r", encoding='utf-8') as f: return json.load(f)

def write_db(file_key, data):
    with open(DB_FILES[file_key], "w", encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

def apply_ui_settings():
    config = read_db("config")
    ctk.set_appearance_mode(config.get("appearance_mode", "dark"))
    ctk.set_default_color_theme(config.get("color_theme", "blue"))

def create_pdf_with_logo(business_name, title, content, filename, align='C'):
    pdf = FPDF()
    pdf.add_page()
    logo_path = resource_path("logo.png")
    if os.path.exists(logo_path):
        page_width = pdf.w - 2 * pdf.l_margin
        pdf.image(logo_path, x=(page_width / 2) + pdf.l_margin - 15, y=8, w=30)
        pdf.ln(30)
    
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, business_name, 0, 1, 'C')
    pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, title, 0, 1, 'C')
    pdf.ln(10)

    pdf.set_font("Courier", size=10)
    pdf.multi_cell(0, 5, txt=content.encode('latin-1', 'replace').decode('latin-1'), align=align)

    pdf.output(filename)
    print(f"Reporte '{filename}' generado.")

# --- Clase Principal de la Aplicación ---
class POSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        apply_ui_settings()
        self.title("Sistema Punto de Venta - Tienda de Ropa"); self.geometry("1200x700")
        self.current_user = None; self.current_user_role = None
        self.container = ctk.CTkFrame(self); self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1); self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}; self.show_frame("LoginScreen")
    def show_frame(self, page_name):
        frame_class = globals().get(page_name)
        if frame_class:
            frame = frame_class(parent=self.container, controller=self)
            self.frames[page_name] = frame; frame.grid(row=0, column=0, sticky="nsew"); frame.tkraise()

    def login(self, username_raw, password):
        username = username_raw.strip().lower()
        users = read_db("users")
        if username in users and users[username]["password"] == password:
            self.current_user = username; self.current_user_role = users[username]["role"]; self.show_frame("MainScreen")
        else: messagebox.showerror("Error de Autenticación", "Usuario o contraseña incorrectos.")
        
    def logout(self):
        self.current_user = None; self.current_user_role = None
        if "MainScreen" in self.frames: self.frames["MainScreen"].destroy(); del self.frames["MainScreen"]
        self.show_frame("LoginScreen")

# --- Pantalla de Login ---
class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller
        try:
            bg_image_path = resource_path("background.png")
            bg_image = ctk.CTkImage(Image.open(bg_image_path), size=(1200, 700))
            bg_label = ctk.CTkLabel(self, image=bg_image, text=""); bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e: 
            print(f"Error cargando imagen de fondo: {e}")

        login_frame = ctk.CTkFrame(self, corner_radius=20, border_width=2); login_frame.place(relx=0.5, rely=0.5, anchor="center")
        try:
            logo_image_path = resource_path("logo.png")
            logo_image = ctk.CTkImage(light_image=Image.open(logo_image_path), size=(150, 150))
            logo_label = ctk.CTkLabel(login_frame, image=logo_image, text=""); logo_label.pack(pady=20, padx=50)
        except Exception as e:
            print(f"Error cargando logo en login: {e}")
            ctk.CTkLabel(login_frame, text="Boutique El Impulso", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20, padx=50)

        ctk.CTkLabel(login_frame, text=self.get_dynamic_greeting(), font=ctk.CTkFont(size=18)).pack(pady=(0, 20))
        self.username_entry = ctk.CTkEntry(login_frame, placeholder_text="Usuario", width=250); self.username_entry.pack(pady=10, padx=30)
        self.password_entry = ctk.CTkEntry(login_frame, placeholder_text="Contraseña", show="*", width=250); self.password_entry.pack(pady=10, padx=30)
        self.password_entry.bind("<Return>", lambda event: self.controller.login(self.username_entry.get(), self.password_entry.get()))
        ctk.CTkButton(login_frame, text="Ingresar", command=lambda: self.controller.login(self.username_entry.get(), self.password_entry.get())).pack(pady=20, padx=30)
        forgot_password_label = ctk.CTkLabel(login_frame, text="Recuperar contraseña", text_color="#5dadec", cursor="hand2"); forgot_password_label.pack(pady=(0, 20))
        forgot_password_label.bind("<Button-1>", self.forgot_password)
    def get_dynamic_greeting(self):
        h = datetime.datetime.now().hour
        if 5 <= h < 12: return "Buenos días"
        elif 12 <= h < 19: return "Buenas tardes"
        else: return "Buenas noches"
    def forgot_password(self, event):
        username = simpledialog.askstring("Recuperar Contraseña", "Ingrese su nombre de usuario:", parent=self)
        if username and username in (users := read_db("users")):
            messagebox.showinfo("Contraseña", f"La contraseña para '{username}' es: {users[username]['password']}")
        elif username: messagebox.showerror("Error", "El usuario no fue encontrado.")

# --- Pantalla Principal (Punto de Venta) ---
class MainScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller
        self.current_sale_items = []
        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=2); self.grid_rowconfigure(1, weight=1)
        top_bar = ctk.CTkFrame(self, height=50, corner_radius=0); top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        try:
            logo_image_path = resource_path("logo.png")
            logo_img = ctk.CTkImage(Image.open(logo_image_path), size=(40, 40))
            ctk.CTkLabel(top_bar, image=logo_img, text="").pack(side="left", padx=10, pady=5)
        except Exception as e:
            print(f"Error cargando logo en pantalla principal: {e}")

        ctk.CTkButton(top_bar, text="Menú", command=self.open_menu).pack(side="left", padx=10, pady=10)
        self.time_user_label = ctk.CTkLabel(top_bar, text="", font=ctk.CTkFont(size=14)); self.time_user_label.pack(side="right", padx=10, pady=10)
        self.update_time()
        # BOTÓN SALIR MODIFICADO
        ctk.CTkButton(top_bar, text="SALIR", command=self.controller.logout, fg_color="#c0392b", hover_color="#e74c3c").pack(side="right", padx=10, pady=10)
        sale_panel = ctk.CTkFrame(self, corner_radius=10); sale_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        sale_panel.grid_rowconfigure(3, weight=1); sale_panel.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(sale_panel, text="Cliente (Opcional):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.customer_name_entry = ctk.CTkEntry(sale_panel, placeholder_text="Nombre del cliente"); self.customer_name_entry.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(sale_panel, text="Añadir Producto:").grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="w")
        self.product_search_entry = ctk.CTkEntry(sale_panel, placeholder_text="Escanear o buscar por nombre/SKU"); self.product_search_entry.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.product_search_entry.bind("<KeyRelease>", self.update_suggestions)
        self.product_search_entry.bind("<Return>", self.add_product_from_scanner_or_selection)
        self.suggestions_toplevel = None

        cart_panel = ctk.CTkFrame(self, corner_radius=10); cart_panel.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        cart_panel.grid_columnconfigure(0, weight=1); cart_panel.grid_rowconfigure(0, weight=1)
        self.cart_listbox = Listbox(cart_panel, bg="#2b2b2b", fg="white", border=0, selectbackground="#1f6aa5", font=("Courier", 14)); self.cart_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        cart_scrollbar = ctk.CTkScrollbar(cart_panel, command=self.cart_listbox.yview); cart_scrollbar.grid(row=0, column=1, sticky="ns"); self.cart_listbox.configure(yscrollcommand=cart_scrollbar.set)
        cart_actions_frame = ctk.CTkFrame(cart_panel, fg_color="transparent"); cart_actions_frame.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkButton(cart_actions_frame, text="Modificar Cantidad", command=self.modify_quantity).pack(side="left", padx=5)
        ctk.CTkButton(cart_actions_frame, text="Eliminar Artículo", command=self.remove_item).pack(side="left", padx=5)
        total_panel = ctk.CTkFrame(cart_panel); total_panel.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        total_panel.grid_columnconfigure(0, weight=1); total_panel.grid_columnconfigure(1, weight=1)
        self.subtotal_label = ctk.CTkLabel(total_panel, text="Subtotal: $0.00", font=ctk.CTkFont(size=20, weight="bold")); self.subtotal_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkButton(total_panel, text="Pagar", font=ctk.CTkFont(size=18), command=self.open_payment_window).grid(row=0, column=1, padx=10, pady=10, sticky="e")

    def update_suggestions(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        search_term = self.product_search_entry.get().lower()
        if not search_term:
            self.hide_suggestions()
            return
        inventory = read_db("inventory")
        matches = {sku: data for sku, data in inventory.items() if search_term in data["name"].lower() or search_term in sku.lower()}
        if matches:
            if not self.suggestions_toplevel:
                self.create_suggestions_toplevel()
            self.suggestions_listbox.delete(0, END)
            for sku, data in matches.items():
                self.suggestions_listbox.insert(END, f"{data['name']} [{sku}]")
        else:
            self.hide_suggestions()
            
    def create_suggestions_toplevel(self):
        entry_x = self.product_search_entry.winfo_rootx()
        entry_y = self.product_search_entry.winfo_rooty() + self.product_search_entry.winfo_height()
        entry_width = self.product_search_entry.winfo_width()
        self.suggestions_toplevel = Toplevel(self)
        self.suggestions_toplevel.overrideredirect(True)
        self.suggestions_toplevel.geometry(f"{entry_width}x150+{entry_x}+{entry_y}")
        self.suggestions_listbox = Listbox(self.suggestions_toplevel, bg="#343638", fg="white", selectbackground="#1f6aa5", border=1, relief="solid")
        self.suggestions_listbox.pack(expand=True, fill="both")
        self.suggestions_listbox.bind("<ButtonRelease-1>", self.add_product_from_scanner_or_selection)
        self.product_search_entry.bind("<Down>", self.focus_suggestions)
        self.suggestions_listbox.bind("<Return>", self.add_product_from_scanner_or_selection)
        self.suggestions_listbox.bind("<Escape>", lambda e: self.hide_suggestions())

    def hide_suggestions(self):
        if self.suggestions_toplevel:
            self.suggestions_toplevel.destroy()
            self.suggestions_toplevel = None

    def focus_suggestions(self, event):
        if self.suggestions_toplevel:
            self.suggestions_listbox.focus_set()
            self.suggestions_listbox.selection_set(0)

    def add_product_from_scanner_or_selection(self, event=None):
        search_term = ""
        if self.suggestions_toplevel and self.suggestions_listbox.curselection():
            selection = self.suggestions_listbox.get(self.suggestions_listbox.curselection())
            search_term = selection.split('[')[-1].strip(']')
        else:
            search_term = self.product_search_entry.get().strip()
        if search_term:
            self.add_product_to_cart(search_term)
            self.product_search_entry.delete(0, 'end')
            self.hide_suggestions()
    
    def add_product_to_cart(self, sku_to_add):
        inventory = read_db("inventory")
        sku_to_add = sku_to_add.upper()
        if sku_to_add in inventory:
            found_product = inventory[sku_to_add]
            existing_item = next((item for item in self.current_sale_items if item["sku"] == sku_to_add), None)
            if existing_item:
                if inventory[sku_to_add]["quantity"] > existing_item["quantity"]:
                    existing_item["quantity"] += 1
                else: messagebox.showwarning("Sin Stock", "No hay más stock disponible.")
            else:
                if inventory[sku_to_add]["quantity"] > 0:
                    self.current_sale_items.append({"sku": sku_to_add, "name": found_product["name"], "price": found_product["price"], "quantity": 1})
                else: messagebox.showwarning("Sin Stock", "El producto está agotado.")
            self.update_cart_display()
        else:
            messagebox.showerror("No Encontrado", f"No se encontró producto con SKU '{sku_to_add}'.")

    def update_time(self): self.time_user_label.configure(text=f"Usuario: {self.controller.current_user} | Hora: {time.strftime('%H:%M:%S')}"); self.after(1000, self.update_time)
    def update_cart_display(self):
        self.cart_listbox.delete(0, END); subtotal = 0
        for i, item in enumerate(self.current_sale_items):
            total_item_price = item["price"] * item["quantity"]
            display_text = f"{item['quantity']:>3}x {item['name']:<35} @ ${item['price']:<8.2f} = ${total_item_price:>8.2f}"
            self.cart_listbox.insert(END, display_text); subtotal += total_item_price
        self.subtotal_label.configure(text=f"Subtotal: ${subtotal:.2f}")

    def get_selected_item_index(self):
        if not (selected_indices := self.cart_listbox.curselection()):
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un artículo de la lista."); return None
        return selected_indices[0]

    def modify_quantity(self):
        if (index := self.get_selected_item_index()) is None: return
        item = self.current_sale_items[index]; inventory = read_db("inventory"); stock_disponible = inventory[item['sku']]['quantity']
        new_quantity = simpledialog.askinteger("Modificar Cantidad", f"Ingrese la nueva cantidad para '{item['name']}'\n(Stock disponible: {stock_disponible})", parent=self, minvalue=1, maxvalue=stock_disponible)
        if new_quantity is not None: item['quantity'] = new_quantity; self.update_cart_display()

    def remove_item(self):
        if (index := self.get_selected_item_index()) is None: return
        if messagebox.askyesno("Confirmar", f"¿Seguro que desea eliminar '{self.current_sale_items[index]['name']}' de la venta?"):
            del self.current_sale_items[index]; self.update_cart_display()

    def open_payment_window(self):
        if not self.current_sale_items: messagebox.showwarning("Venta Vacía", "Agregue productos antes de cobrar."); return
        subtotal = sum(item['price'] * item['quantity'] for item in self.current_sale_items)
        PaymentWindow(self, subtotal)

    def finalize_sale(self, payment_method, total, details):
        config = read_db("config")
        new_ticket_number = config.get("last_ticket_number", 0) + 1
        sales = read_db("sales")
        sale_record = {"ticket_number": new_ticket_number, "timestamp": datetime.datetime.now().isoformat(), "user": self.controller.current_user, "items": self.current_sale_items, "total": total, "payment_method": payment_method, "details": details, "status": "COMPLETADA"}
        sales.append(sale_record); write_db("sales", sales)
        config["last_ticket_number"] = new_ticket_number
        write_db("config", config)
        inventory = read_db("inventory")
        for item in self.current_sale_items:
            if item["sku"] in inventory: inventory[item["sku"]]["quantity"] -= item["quantity"]
        write_db("inventory", inventory); ShippingOptionsWindow(self, sale_record)
    
    def reset_sale_screen(self):
        self.current_sale_items = []; self.update_cart_display(); self.customer_name_entry.delete(0, 'end'); self.product_search_entry.delete(0, 'end')

    def generate_ticket_text(self, sale_record):
        header = (f"Ticket N°: {sale_record['ticket_number']}\n"
                  f"Fecha: {datetime.datetime.fromisoformat(sale_record['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                  f"Atendido por: {sale_record['user']}\n"
                  f"----------------------------------------\n")
        items_text = ""
        for item in sale_record['items']:
            line = f"{item['quantity']}x {item['name']} - ${item['price'] * item['quantity']:.2f}"
            items_text += line + "\n"
        footer = (f"----------------------------------------\n"
                  f"Metodo de Pago: {sale_record['payment_method']}\n"
                  f"TOTAL: ${sale_record['total']:.2f}\n\n"
                  f"Este ticket de compra NO ES UN COMPROBANTE FISCAL.\n"
                  f"Para Devoluciones solamente se cuenta con 7\n"
                  f"días naturales a partir de la fecha de compra.\n")
        return header + items_text + footer

    def open_menu(self): MenuWindow(self)

class ShippingOptionsWindow(ctk.CTkToplevel):
    def __init__(self, master, sale_record):
        super().__init__(master); self.master_screen = master; self.sale_record = sale_record
        self.title("Método de Envío del Ticket"); self.geometry("450x200"); self.transient(master); self.grab_set()
        ctk.CTkLabel(self, text="Seleccione el método de envío del ticket", font=ctk.CTkFont(size=16)).pack(pady=20, padx=20)
        button_frame = ctk.CTkFrame(self, fg_color="transparent"); button_frame.pack(pady=10)
        ctk.CTkButton(button_frame, text="Imprimir Ticket en PDF", command=self.print_to_pdf, height=40).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Enviar por Correo Electrónico", command=self.send_by_email, height=40).pack(side="left", padx=10)
    def print_to_pdf(self):
        ticket_text = self.master_screen.generate_ticket_text(self.sale_record)
        ticket_filename = f"tickets/venta_{self.sale_record['ticket_number']}.pdf"
        os.makedirs("tickets", exist_ok=True)
        create_pdf_with_logo("Boutique El Impulso", "Ticket de Venta", ticket_text, ticket_filename)
        messagebox.showinfo("Éxito", f"Ticket guardado como:\n{ticket_filename}")
        self.master_screen.reset_sale_screen(); self.destroy()
    def send_by_email(self): EmailTicketWindow(self, self.sale_record, self.master_screen)

class EmailTicketWindow(ctk.CTkToplevel):
    def __init__(self, master, sale_record, main_screen):
        super().__init__(master)
        self.master = master; self.sale_record = sale_record; self.main_screen = main_screen
        self.title("Enviar Ticket por Correo"); self.geometry("400x300"); self.transient(master); self.grab_set()
        ctk.CTkLabel(self, text="Correo Electrónico del Cliente:", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.email_entry = ctk.CTkEntry(self, placeholder_text="ejemplo@correo.com", width=300); self.email_entry.pack()
        button_frame = ctk.CTkFrame(self, fg_color="transparent"); button_frame.pack(pady=20)
        self.send_button = ctk.CTkButton(button_frame, text="Enviar Ticket", command=lambda: self.handle_send_email(False))
        self.send_button.pack(side="left", padx=10, ipady=5)
        self.resend_button = ctk.CTkButton(button_frame, text="Reenviar Ticket", command=lambda: self.handle_send_email(True))
        self.resend_button.pack(side="left", padx=10, ipady=5)
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(pady=(0, 10))
    def handle_send_email(self, is_resend=False):
        email_address = self.email_entry.get().strip()
        if not email_address:
            messagebox.showerror("Error", "Por favor, ingrese una dirección de correo.", parent=self); return
        self.send_button.configure(state="disabled", text="Enviando...")
        self.resend_button.configure(state="disabled")
        self.status_label.configure(text="Generando ticket y conectando...")
        self.update_idletasks()
        safe_timestamp = str(self.sale_record['ticket_number'])
        ticket_filename = f"temp_ticket_{safe_timestamp}.pdf"
        try:
            ticket_text = self.main_screen.generate_ticket_text(self.sale_record)
            create_pdf_with_logo("Boutique El Impulso", "Ticket de Venta", ticket_text, ticket_filename)
            config = read_db("email")
            if config["sender_email"] == "tu_correo@gmail.com":
                 messagebox.showerror("Configuración Requerida", "Debe configurar 'email_config.json' antes de enviar correos.", parent=self); return
            self.send_email_logic(recipient=email_address, subject="Su Ticket de Compra - Boutique El Impulso", body="¡Hola!\n\nAdjunto encontrará su ticket de compra.\n\nGracias por su preferencia.", attachment_path=ticket_filename, config=config)
            messagebox.showinfo("Éxito", "Ticket enviado correctamente.")
            self.main_screen.reset_sale_screen(); self.master.destroy(); self.destroy()
        except FileNotFoundError: messagebox.showerror("Error de Configuración", "No se encontró 'email_config.json'.", parent=self)
        except smtplib.SMTPAuthenticationError: messagebox.showerror("Error de Autenticación", "La combinación de correo y contraseña de aplicación es incorrecta. Verifique 'email_config.json'.", parent=self)
        except (socket.gaierror, ConnectionRefusedError): messagebox.showerror("Error de Conexión", "No se pudo conectar al servidor de correo. Verifique su conexión a internet.", parent=self)
        except Exception as e: messagebox.showerror("Error de Envío", f"Ocurrió un error inesperado:\n{e}", parent=self)
        finally:
            self.send_button.configure(state="normal", text="Enviar Ticket")
            self.resend_button.configure(state="normal")
            self.status_label.configure(text="")
            if os.path.exists(ticket_filename): os.remove(ticket_filename)
    def send_email_logic(self, recipient, subject, body, attachment_path, config):
        msg = MIMEMultipart()
        msg['From'] = f"Boutique El Impulso <{config['sender_email']}>"; msg['To'] = recipient; msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream"); part.set_payload(attachment.read())
        encoders.encode_base64(part); part.add_header("Content-Disposition", f"attachment; filename=ticket_compra.pdf")
        msg.attach(part)
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port']); server.starttls()
        server.login(config['sender_email'], config['sender_password'])
        server.sendmail(config['sender_email'], recipient, msg.as_string())
        server.quit()

class PaymentWindow(ctk.CTkToplevel):
    def __init__(self, master, total_amount):
        super().__init__(master); self.master_screen = master; self.total_amount = total_amount
        self.title("Método de Pago"); self.geometry("400x350"); self.transient(master); self.grab_set()
        ctk.CTkLabel(self, text=f"Total a Pagar: ${self.total_amount:.2f}", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)
        self.payment_method = ctk.StringVar(value="Efectivo")
        ctk.CTkOptionMenu(self, variable=self.payment_method, values=["Efectivo", "Tarjeta Bancaria", "Transferencia"], command=self.update_payment_fields).pack(pady=10)
        self.fields_frame = ctk.CTkFrame(self); self.fields_frame.pack(pady=10, padx=20, fill="x"); self.update_payment_fields()
    def update_payment_fields(self, *args):
        for widget in self.fields_frame.winfo_children(): widget.destroy()
        if (method := self.payment_method.get()) == "Efectivo":
            ctk.CTkLabel(self.fields_frame, text="Monto Recibido:").pack(pady=5)
            self.amount_received_entry = ctk.CTkEntry(self.fields_frame, justify="center"); self.amount_received_entry.pack(); self.amount_received_entry.bind("<KeyRelease>", self.calculate_change)
            self.change_label = ctk.CTkLabel(self.fields_frame, text="Cambio: $0.00", font=ctk.CTkFont(size=16)); self.change_label.pack(pady=10)
        else:
            ctk.CTkLabel(self.fields_frame, text="Folio de Transacción:").pack(pady=5); self.folio_entry = ctk.CTkEntry(self.fields_frame, justify="center"); self.folio_entry.pack()
        ctk.CTkButton(self, text="Confirmar Pago", command=self.process_payment).pack(pady=20)
    def calculate_change(self, event=None):
        try: self.change_label.configure(text=f"Cambio: ${float(self.amount_received_entry.get()) - self.total_amount:.2f}")
        except (ValueError, TypeError): self.change_label.configure(text="Cambio: $0.00")
    def process_payment(self):
        method, details = self.payment_method.get(), {}
        if method == "Efectivo":
            try:
                if (received := float(self.amount_received_entry.get())) < self.total_amount: messagebox.showerror("Error", "El monto recibido es menor al total."); return
                details = {"received": received, "change": received - self.total_amount}
            except ValueError: messagebox.showerror("Error", "Ingrese un monto válido."); return
        else:
            if not (folio := self.folio_entry.get().strip()): messagebox.showerror("Error", "El folio es obligatorio."); return
            details = {"folio": folio}
        self.master_screen.finalize_sale(method, self.total_amount, details); self.destroy()

class MenuWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master); self.master_app = master.controller
        self.title("Menú de Opciones"); self.geometry("300x500"); self.transient(master); self.grab_set()
        ctk.CTkLabel(self, text="Opciones del Sistema", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        buttons_info = [("Ajustes del programa", self.open_settings), ("Devolución", self.open_return_window), ("Dar de alta/Baja usuario", self.open_user_manager), ("Administrar inventario", self.open_inventory_manager), ("Corte de caja", self.open_cash_count)]
        for text, command in buttons_info: ctk.CTkButton(self, text=text, command=command, height=40).pack(pady=10, padx=20, fill="x")
    def check_admin_role(self):
        if self.master_app.current_user_role != "administrador": messagebox.showerror("Acceso Denegado", "Opción solo para administradores."); return False
        return True
    def open_settings(self): SettingsWindow(self)
    def open_return_window(self): ReturnWindow(self)
    def open_user_manager(self): 
        if self.check_admin_role(): UserManagerWindow(self)
    def open_inventory_manager(self):
        if self.check_admin_role(): InventoryManagerWindow(self)
    def open_cash_count(self): CashCountWindow(self)

class ReturnWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Gestión de Devoluciones"); self.geometry("600x500"); self.transient(master); self.grab_set()
        self.found_sale = None
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(top_frame, text="Ingrese Número de Ticket:").pack(side="left", padx=5)
        self.ticket_entry = ctk.CTkEntry(top_frame, placeholder_text="Ej: 123")
        self.ticket_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.ticket_entry.bind("<Return>", lambda e: self.search_ticket())
        ctk.CTkButton(top_frame, text="Buscar Ticket", command=self.search_ticket).pack(side="left", padx=5)
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.info_text = ctk.CTkTextbox(info_frame, state="disabled", font=("Courier", 12))
        self.info_text.pack(fill="both", expand=True)
        self.return_button = ctk.CTkButton(self, text="Realizar Devolución", command=self.process_return, state="disabled")
        self.return_button.pack(pady=10, padx=10)
    def search_ticket(self):
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", END)
        self.found_sale = None
        self.return_button.configure(state="disabled")
        try:
            ticket_number = int(self.ticket_entry.get())
        except ValueError:
            messagebox.showerror("Error", "El número de ticket debe ser un número válido.", parent=self)
            return
        sales = read_db("sales")
        sale_found = next((s for s in sales if s.get("ticket_number") == ticket_number), None)
        if not sale_found:
            self.info_text.insert("1.0", f"No se encontró ninguna venta con el ticket N° {ticket_number}.")
            self.info_text.configure(state="disabled")
            return
        self.found_sale = sale_found
        sale_date = datetime.datetime.fromisoformat(sale_found["timestamp"])
        days_since_purchase = (datetime.datetime.now() - sale_date).days
        info = (f"Ticket N°: {sale_found['ticket_number']}\n"
            f"Fecha de Compra: {sale_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Días desde la compra: {days_since_purchase}\n"
            f"Cliente: {sale_found.get('customer_name', 'N/A')}\n"
            f"Total: ${sale_found['total']:.2f}\n"
            f"Estado: {sale_found['status']}\n"
            f"----------------------------------------\n")
        for item in sale_found["items"]:
            info += f"{item['quantity']}x {item['name']} - ${item['price'] * item['quantity']:.2f}\n"
        self.info_text.insert("1.0", info)
        if sale_found['status'] == 'DEVUELTA':
            self.info_text.insert(END, "\nERROR: Este ticket ya ha sido devuelto.")
        elif days_since_purchase > 7:
            self.info_text.insert(END, f"\nERROR: Han pasado más de 7 días. No se puede realizar la devolución.")
        else:
            self.return_button.configure(state="normal")
        self.info_text.configure(state="disabled")
    def process_return(self):
        if not self.found_sale: return
        if not messagebox.askyesno("Confirmar Devolución", "¿Está seguro de realizar la devolución de este ticket?", parent=self):
            return
        inventory = read_db("inventory")
        for item in self.found_sale["items"]:
            if item["sku"] in inventory:
                inventory[item["sku"]]["quantity"] += item["quantity"]
        write_db("inventory", inventory)
        sales = read_db("sales")
        for sale in sales:
            if sale.get("ticket_number") == self.found_sale["ticket_number"]:
                sale["status"] = "DEVUELTA"
                break
        write_db("sales", sales)
        messagebox.showinfo("Éxito", "Devolución procesada correctamente.\nEl inventario y el registro de ventas han sido actualizados.", parent=self)
        self.destroy()

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Ajustes del Programa"); self.geometry("400x500"); self.transient(master); self.grab_set()
        ctk.CTkLabel(self, text="Ajustes", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.config = read_db("config")
        appearance_frame = ctk.CTkFrame(self); appearance_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(appearance_frame, text="Modo de Apariencia:").pack(anchor="w", padx=10)
        self.appearance_mode_var = ctk.StringVar(value=self.config.get("appearance_mode", "dark"))
        ctk.CTkOptionMenu(appearance_frame, variable=self.appearance_mode_var, values=["light", "dark", "system"], command=self.change_appearance).pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(appearance_frame, text="Tema de Color:").pack(anchor="w", padx=10, pady=(10,0))
        self.color_theme_var = ctk.StringVar(value=self.config.get("color_theme", "blue"))
        ctk.CTkOptionMenu(appearance_frame, variable=self.color_theme_var, values=["blue", "dark-blue", "green"], command=self.change_theme).pack(fill="x", padx=10, pady=5)
        program_frame = ctk.CTkFrame(self); program_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(program_frame, text="Mantenimiento y Pruebas:").pack(anchor="w", padx=10)
        ctk.CTkButton(program_frame, text="Probar Conexión de Correo", command=self.test_email_connection).pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(program_frame, text="Restablecer Programa", fg_color="#c0392b", hover_color="#e74c3c", command=self.reset_program).pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(self, text="Nota: Se requiere reiniciar para ver\ntodos los cambios de apariencia.", justify="center").pack(pady=10)
    def change_appearance(self, mode): ctk.set_appearance_mode(mode); self.config["appearance_mode"] = mode; write_db("config", self.config)
    def change_theme(self, theme): messagebox.showinfo("Cambio de Tema", "El cambio se aplicará al reiniciar."); self.config["color_theme"] = theme; write_db("config", self.config)
    def reset_program(self):
        if messagebox.askyesno("Confirmar", "¡ADVERTENCIA!\nEsto borrará TODOS los datos.\n¿Está seguro?"):
            for file in DB_FILES.values():
                if os.path.exists(file): os.remove(file)
            messagebox.showinfo("Éxito", "Programa restablecido. Se reiniciará."); os.execv(sys.executable, ['python'] + sys.argv)
    def test_email_connection(self):
        try:
            config = read_db("email")
            if config["sender_email"] == "tu_correo@gmail.com":
                 messagebox.showerror("Configuración Requerida", "Debe configurar 'email_config.json' antes de probar.", parent=self); return
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls(); server.login(config['sender_email'], config['sender_password'])
            messagebox.showinfo("Éxito", "¡Conexión exitosa!\nEl servidor de correo respondió correctamente.", parent=self)
        except smtplib.SMTPAuthenticationError: messagebox.showerror("Error de Autenticación", "Correo o contraseña de aplicación incorrectos.", parent=self)
        except (socket.gaierror, ConnectionRefusedError): messagebox.showerror("Error de Conexión", "No se pudo conectar al servidor. Verifique internet y el nombre del servidor.", parent=self)
        except Exception as e: messagebox.showerror("Error", f"Ocurrió un error:\n{e}", parent=self)

class UserManagerWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Administración de Usuarios"); self.geometry("600x400"); self.transient(master); self.grab_set()
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)
        list_frame = ctk.CTkFrame(self); list_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        list_frame.grid_columnconfigure(0, weight=1); list_frame.grid_rowconfigure(0, weight=1)
        self.user_listbox = Listbox(list_frame, bg="#2b2b2b", fg="white", border=0, selectbackground="#1f6aa5"); self.user_listbox.grid(row=0, column=0, sticky="nsew")
        actions_frame = ctk.CTkFrame(self); actions_frame.grid(row=0, column=1, sticky="ns", padx=10, pady=10)
        ctk.CTkButton(actions_frame, text="Añadir Usuario", command=self.add_user).pack(pady=5, fill="x")
        ctk.CTkButton(actions_frame, text="Eliminar Usuario", command=self.remove_user).pack(pady=5, fill="x")
        ctk.CTkButton(actions_frame, text="Cambiar Contraseña", command=self.change_password).pack(pady=5, fill="x")
        self.refresh_user_list()
    def refresh_user_list(self):
        self.user_listbox.delete(0, END)
        users = read_db("users")
        for username, data in users.items():
            self.user_listbox.insert(END, f"{username} ({data['role']})")
    def add_user(self):
        username_raw = simpledialog.askstring("Añadir Usuario", "Nombre de usuario:", parent=self)
        if not username_raw: return
        username = username_raw.strip().lower()
        if not username: return 
        users = read_db("users")
        if username in users:
            messagebox.showerror("Error", f"El nombre de usuario '{username}' ya existe.", parent=self)
            return
        password = simpledialog.askstring("Añadir Usuario", "Contraseña:", parent=self, show="*")
        if not password: return
        role = simpledialog.askstring("Añadir Usuario", "Rol (administrador/vendedor):", parent=self)
        if role and role.lower() in ["administrador", "vendedor"]:
             users[username] = {"password": password, "role": role.lower()}
             write_db("users", users)
             self.refresh_user_list()
        else:
             messagebox.showerror("Error", "Rol no válido. Debe ser 'administrador' o 'vendedor'.", parent=self)
    def remove_user(self):
        selected = self.user_listbox.curselection()
        if not selected: messagebox.showwarning("Sin Selección", "Seleccione un usuario para eliminar.", parent=self); return
        username = self.user_listbox.get(selected[0]).split(" ")[0]
        if username == "admin": messagebox.showerror("Error", "No se puede eliminar al usuario administrador principal.", parent=self); return
        if messagebox.askyesno("Confirmar", f"¿Seguro que desea eliminar al usuario '{username}'?", parent=self):
            users = read_db("users"); del users[username]; write_db("users", users); self.refresh_user_list()
    def change_password(self):
        selected = self.user_listbox.curselection()
        if not selected: messagebox.showwarning("Sin Selección", "Seleccione un usuario.", parent=self); return
        username = self.user_listbox.get(selected[0]).split(" ")[0]
        new_password = simpledialog.askstring("Nueva Contraseña", f"Ingrese la nueva contraseña para '{username}':", parent=self, show="*")
        if new_password:
            users = read_db("users"); users[username]["password"] = new_password; write_db("users", users)
            messagebox.showinfo("Éxito", f"Contraseña de '{username}' actualizada.", parent=self)

# --- VENTANA DE INVENTARIO MODIFICADA ---
class InventoryManagerWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Administración de Inventario"); self.geometry("850x600"); self.transient(master); self.grab_set() # Ancho ajustado
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        
        top_frame = ctk.CTkFrame(self); top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(top_frame, text="SKU:").pack(side="left", padx=5); self.sku_entry = ctk.CTkEntry(top_frame, placeholder_text="Escanear o ingresar SKU"); self.sku_entry.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(top_frame, text="Nombre:").pack(side="left", padx=5); self.name_entry = ctk.CTkEntry(top_frame, placeholder_text="Nombre del producto"); self.name_entry.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(top_frame, text="Precio:").pack(side="left", padx=5); self.price_entry = ctk.CTkEntry(top_frame, placeholder_text="0.00", width=80); self.price_entry.pack(side="left", padx=5)
        ctk.CTkLabel(top_frame, text="Cantidad:").pack(side="left", padx=5); self.quantity_entry = ctk.CTkEntry(top_frame, placeholder_text="0", width=80); self.quantity_entry.pack(side="left", padx=5)
        # BOTÓN "AÑADIR" CON ANCHO CORREGIDO
        ctk.CTkButton(top_frame, text="Añadir/Actualizar", command=self.add_update_item, width=140).pack(side="left", padx=10)
        self.sku_entry.bind("<Return>", lambda e: self.add_update_item())

        tree_frame = ctk.CTkFrame(self); tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.grid_columnconfigure(0, weight=1); tree_frame.grid_rowconfigure(0, weight=1)
        style = ttk.Style(); style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f6aa5')])
        self.tree = ttk.Treeview(tree_frame, columns=("SKU", "Nombre", "Precio", "Cantidad"), show="headings")
        self.tree.heading("SKU", text="SKU"); self.tree.heading("Nombre", text="Nombre"); self.tree.heading("Precio", text="Precio"); self.tree.heading("Cantidad", text="Cantidad")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        bottom_frame = ctk.CTkFrame(self); bottom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkButton(bottom_frame, text="Guardar como PDF", command=self.save_pdf).pack(side="left", padx=10)
        # BOTÓN "EDITAR" AÑADIDO
        ctk.CTkButton(bottom_frame, text="Editar Descripción", command=self.edit_item_description).pack(side="left", padx=10)
        ctk.CTkButton(bottom_frame, text="Eliminar Producto", command=self.remove_item, fg_color="#c0392b", hover_color="#e74c3c").pack(side="left", padx=10)
        self.refresh_inventory_list()

    def refresh_inventory_list(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        inventory = read_db("inventory")
        for sku, data in sorted(inventory.items()): # Ordenado por SKU
            self.tree.insert("", "end", values=(sku, data["name"], f"${data['price']:.2f}", data["quantity"]))
    
    def add_update_item(self):
        sku = self.sku_entry.get().strip().upper()
        name = self.name_entry.get().strip()
        price = self.price_entry.get().strip()
        quantity = self.quantity_entry.get().strip()
        if not all([sku, name, price, quantity]): messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=self); return
        try: price_val, quant_val = float(price), int(quantity)
        except ValueError: messagebox.showerror("Error", "Precio y Cantidad deben ser números.", parent=self); return
        inventory = read_db("inventory")
        inventory[sku] = {"name": name, "price": price_val, "quantity": quant_val}
        write_db("inventory", inventory); self.refresh_inventory_list()
        self.sku_entry.delete(0, END); self.name_entry.delete(0, END); self.price_entry.delete(0, END); self.quantity_entry.delete(0, END)
        self.sku_entry.focus()
    
    # FUNCIÓN "EDITAR" AÑADIDA
    def edit_item_description(self):
        selected_item = self.tree.focus() 
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un producto de la lista para editar.", parent=self)
            return
        
        item_details = self.tree.item(selected_item)
        sku = item_details['values'][0]
        current_name = item_details['values'][1]

        new_name = simpledialog.askstring("Editar Descripción", f"Ingrese el nuevo nombre para el producto SKU: {sku}", initialvalue=current_name, parent=self)

        if new_name and new_name.strip() != "":
            inventory = read_db("inventory")
            if sku in inventory:
                inventory[sku]['name'] = new_name.strip()
                write_db("inventory", inventory)
                self.refresh_inventory_list()
                messagebox.showinfo("Éxito", "Descripción del producto actualizada.", parent=self)
        elif new_name is not None: # Si el usuario borra el texto y presiona OK
            messagebox.showerror("Error", "La descripción no puede estar vacía.", parent=self)

    def remove_item(self):
        selected_item = self.tree.focus() 
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un producto de la lista para eliminar.", parent=self)
            return
        item_details = self.tree.item(selected_item)
        sku = item_details['values'][0]
        product_name = item_details['values'][1]
        if messagebox.askyesno("Confirmar Eliminación", f"¿Seguro que quieres eliminar el producto '{product_name}'?", parent=self):
            inventory = read_db("inventory")
            if sku in inventory:
                del inventory[sku]
                write_db("inventory", inventory)
                self.refresh_inventory_list()
                messagebox.showinfo("Éxito", "Producto eliminado correctamente.", parent=self)
            else:
                messagebox.showerror("Error", "El producto no se encontró en la base de datos.", parent=self)
    
    def save_pdf(self):
        inventory = read_db("inventory")
        content = f"{'SKU':<15}{'Nombre':<35}{'Precio':>10}{'Cantidad':>10}\n"
        content += "-" * 70 + "\n"
        for sku, data in sorted(inventory.items()):
            content += f"{sku:<15}{data['name']:<35}${data['price']:>9.2f}{data['quantity']:>10}\n"
        os.makedirs("reportes", exist_ok=True)
        filename = f"reportes/inventario_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
        create_pdf_with_logo("Boutique El Impulso", "Reporte de Inventario", content, filename, align='L')
        messagebox.showinfo("Éxito", f"Reporte guardado como {filename}", parent=self)

class CashCountWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.controller = master.master_app
        self.title("Corte de Caja"); self.geometry("500x450"); self.transient(master); self.grab_set()
        ctk.CTkLabel(self, text="Corte de Caja Diario", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(self, text=f"Usuario: {self.controller.current_user}").pack()
        ctk.CTkLabel(self, text=f"Fecha y Hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}").pack()
        self.summary_label = ctk.CTkLabel(self, text="--- Calculando... ---", justify="left", font=ctk.CTkFont(family="Courier", size=14))
        self.summary_label.pack(pady=20)
        self.calculate_daily_sales()
        ctk.CTkButton(self, text="Iniciar Corte de Caja y Salir", command=self.perform_cash_count, height=40).pack(pady=10, padx=20, fill="x")
    def calculate_daily_sales(self):
        sales = read_db("sales"); today = datetime.date.today()
        daily_sales = [s for s in sales if datetime.datetime.fromisoformat(s['timestamp']).date() == today and s.get("status") == "COMPLETADA"]
        daily_returns = [s for s in sales if datetime.datetime.fromisoformat(s['timestamp']).date() == today and s.get("status") == "DEVUELTA"]
        total_cash = sum(s['total'] for s in daily_sales if s['payment_method'] == 'Efectivo')
        total_card = sum(s['total'] for s in daily_sales if s['payment_method'] == 'Tarjeta Bancaria')
        total_transfer = sum(s['total'] for s in daily_sales if s['payment_method'] == 'Transferencia')
        total_day_gross = sum(s['total'] for s in daily_sales)
        total_returned = sum(r['total'] for r in daily_returns)
        net_total = total_day_gross - total_returned
        summary_text = (f"-- Desglose de Ventas --\n\n"
            f"Ventas en Efectivo:    ${total_cash:10.2f}\n"
            f"Ventas con Tarjeta:    ${total_card:10.2f}\n"
            f"Ventas con Transferencia:${total_transfer:10.2f}\n"
            f"----------------------------------\n"
            f"Total Ventas Bruto:    ${total_day_gross:10.2f}\n\n"
            f"Devoluciones del Día:  -${total_returned:10.2f}\n"
            f"==================================\n"
            f"Total Neto en Caja:    ${net_total:10.2f}")
        self.summary_label.configure(text=summary_text)
    def perform_cash_count(self):
        if not messagebox.askyesno("Confirmar", "¿Está seguro de realizar el corte? El programa se cerrará.", parent=self): return
        report_content = (f"Fecha: {datetime.date.today()}\n"
            f"Usuario: {self.controller.current_user}\n"
            f"Hora: {datetime.datetime.now().strftime('%H:%M:%S')}\n\n"
            f"{self.summary_label.cget('text')}")
        os.makedirs("cortes", exist_ok=True)
        filename = f"cortes/corte_{datetime.date.today()}.pdf"
        create_pdf_with_logo("Boutique El Impulso", "Corte de Caja", report_content, filename, align='L')
        messagebox.showinfo("Corte Realizado", f"El corte de caja se ha guardado en:\n{filename}\n\nEl programa se cerrará ahora.")
        self.controller.quit()

if __name__ == "__main__":
    setup_database()
    app = POSApp()
    app.mainloop()








    





