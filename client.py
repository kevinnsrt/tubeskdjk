import socket
import threading
import customtkinter as ctk
from customtkinter import filedialog
import os

DOWNLOAD_DIR = "downloads"
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

class ChatClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("Dark") 
        ctk.set_default_color_theme("blue")
        
        self.title("NetworkChat")
        self.geometry("800x900")
        self.configure(fg_color="#F1E5D1")  
        
        self.client_socket = None 
        self.username = None
        
        # Create sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, fg_color="#987070", corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y", expand=False)
        self.sidebar_frame.pack_propagate(False)
        
        # Sidebar Title
        self.sidebar_title = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Chat Actions", 
            font=("Arial", 18, "bold"),
            text_color="#F1E5D1"
        )
        self.sidebar_title.pack(pady=(20, 10))
        
        # Create main content frame
        self.main_frame = ctk.CTkFrame(self, fg_color="#F1E5D1", corner_radius=0)
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="OZI DURIAN RUNTUH", 
            font=("Arial", 24, "bold"),
            text_color="#987070"
        )
        self.title_label.pack(pady=(20, 10))
        
        # Username Section with Modern Style
        self.username_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.username_frame.pack(pady=10, padx=20, fill="x")
        
        self.entry_name = ctk.CTkEntry(
            self.username_frame, 
            placeholder_text="Enter your username", 
            width=300,
            fg_color="#DBB5B5",
            border_color="#987070", 
            border_width=2,
            text_color="#987070"
        )
        self.entry_name.pack(side="left", padx=(0, 10))
        
        self.button_connect = ctk.CTkButton(
            self.username_frame, 
            text="Connect",
            text_color="#F1E5D1",
            command=self.connect_to_server,
            fg_color="#987070",
            hover_color="#987070"
        )
        self.button_connect.pack(side="left")
        
        # Chat Box with Enhanced Design
        self.chat_box = ctk.CTkTextbox(
            self.main_frame, 
            height=450, 
            state="disabled",
            fg_color="#DBB5B5", 
            text_color="black",
            border_color="#987070",
            border_width=2
        )
        self.chat_box.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Message Input Section
        self.message_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.message_frame.pack(pady=10, padx=20, fill="x")
        
        self.entry_message = ctk.CTkEntry(
            self.message_frame, 
            placeholder_text="Type your message...", 
            width=400,
            fg_color="#DBB5B5",
            border_color="#987070", 
            border_width=2,
            text_color="#987070"
        )
        self.entry_message.pack(side="left", padx=(0, 10), expand=True)
        
        self.button_send = ctk.CTkButton(
            self.message_frame, 
            text="Send", 
            command=self.send_message,
            fg_color="#987070",
            text_color="#F1E5D1",
            hover_color="#B33C5F",
            width=100
        )
        self.button_send.pack(side="left")
        
        # Sidebar Action Buttons
        sidebar_button_configs = [
            ("Join Group", self.join_group, "#DBB5B5","#987070"),
            ("Group Message", self.send_group_message, "#DBB5B5","#987070"),
            ("Leave Group", self.leave_group, "#DBB5B5","#987070"),
            ("Upload File", self.upload_file, "#DBB5B5","#987070"),
            ("Download File", self.download_file, "#DBB5B5","#987070")
        ]
        
        for text, command, color,text_color in sidebar_button_configs:
            btn = ctk.CTkButton(
                self.sidebar_frame, 
                text=text,
                text_color=text_color, 
                command=command,
                fg_color=color,
                hover_color=f"{color}CC",  # Slightly transparent hover
                corner_radius=6,
                width=180  # Ensure consistent sidebar button width
            )
            btn.pack(pady=10, padx=10)
        
        # Closing Protocol
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    
    def connect_to_server(self):
        """Koneksi ke server"""
        self.username = self.entry_name.get()
        if not self.username:
            self.show_message("Username cannot be empty!")
            return

        try:
            # Buat socket dan hubungkan
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
            
            # Kirim username
            self.client_socket.send(self.username.encode('utf-8'))
            
            # Nonaktifkan input nama setelah koneksi
            self.entry_name.configure(state="disabled")
            self.button_connect.configure(state="disabled")
            
            # Mulai thread penerima pesan
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
            self.show_message(f"Connected to server as {self.username}")
        
        except Exception as e:
            self.show_message(f"Failed to connect to server: {e}")

    def receive_messages(self):
        """Menerima pesan dari server"""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    self.show_message(message)
            except Exception as e:
                self.show_message("Disconnected from server.")
                break

    def send_message(self):
        """Mengirim pesan pribadi"""
        if not self.client_socket:
            self.show_message("Not connected to server.")
            return

        message = self.entry_message.get()
        if message:
            try:
                # Kirim pesan
                self.client_socket.send(message.encode('utf-8'))
                self.entry_message.delete(0, 'end')
            except Exception as e:
                self.show_message(f"Failed to send message: {e}")

    def join_group(self):
        """Bergabung ke group chat"""
        if not self.client_socket:
            self.show_message("Not connected to server.")
            return

        try:
            self.client_socket.send("!group".encode('utf-8'))
            self.show_message("Joining group chat.")
        except Exception as e:
            self.show_message(f"Failed to join group: {e}")

    def send_group_message(self):
        """Mengirim pesan group"""
        if not self.client_socket:
            self.show_message("Not connected to server.")
            return

        message = self.entry_message.get()
        if message:
            try:
                # Kirim pesan group
                self.client_socket.send(f"!g {message}".encode('utf-8'))
                self.entry_message.delete(0, 'end')
            except Exception as e:
                self.show_message(f"Failed to send group message: {e}")

    def leave_group(self):
        """Keluar dari group chat"""
        if not self.client_socket:
            self.show_message("Not connected to server.")
            return

        try:
            self.client_socket.send("!leave".encode('utf-8'))
            self.show_message("Left group chat.")
        except Exception as e:
            self.show_message(f"Failed to leave group: {e}")

    def upload_file(self):
        """Mengunggah file ke server"""
        if not self.client_socket:
            self.show_message("Not connected to server.")
            return

        # Pilih file
        filename = filedialog.askopenfilename()
        if not filename:
            return

        try:
            # Kirim sinyal upload
            self.client_socket.send("UPLOAD".encode('utf-8'))
            
            # Kirim info file
            filesize = os.path.getsize(filename)
            file_info = f"{os.path.basename(filename)}|{filesize}"
            self.client_socket.send(file_info.encode())

            # Kirim file
            with open(filename, 'rb') as f:
                while chunk := f.read(1024):
                    self.client_socket.send(chunk)

            self.show_message(f"File {os.path.basename(filename)} uploaded successfully.")
        
        except Exception as e:
            self.show_message(f"Failed to upload file: {e}")

    def download_file(self):
        """Mengunduh file dari server"""
        if not self.client_socket:
            self.show_message("Not connected to server.")
            return

        # Minta nama file
        filename = self.entry_message.get()
        if not filename:
            self.show_message("Enter a filename to download.")
            return

        try:
            # Kirim sinyal download
            self.client_socket.send("DOWNLOAD".encode('utf-8'))
            self.client_socket.send(filename.encode())

            # Terima respon
            response = self.client_socket.recv(1024)
            
            if response == b"FILE_FOUND":
                # Simpan file di direktori download
                save_path = os.path.join(DOWNLOAD_DIR, filename)
                
                with open(save_path, 'wb') as f:
                    while True:
                        data = self.client_socket.recv(1024)
                        if data == b"EOF":
                            break
                        f.write(data)
                
                self.show_message(f"File {filename} downloaded successfully.")
            else:
                self.show_message(f"File {filename} not found on server.")
        
        except Exception as e:
            self.show_message(f"Failed to download file: {e}")

    def show_message(self, message):
        """Menampilkan pesan di chat box"""
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{message}\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def on_closing(self):
        """Handler saat aplikasi ditutup"""
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.destroy()

if __name__ == "__main__":
    app = ChatClientApp()
    app.mainloop()