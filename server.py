import socket
import threading
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import re

UPLOAD_FOLDER = 'server_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class ChatServer:
    def __init__(self, host='192.168.216.110', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        # Dictionary untuk menyimpan client
        self.clients = {}
        self.groups = []

        # Setup GUI
        self.root = tk.Tk()
        self.root.title(f"Chat Server - {host}:{port}")
        self.root.geometry("600x500")

        # Log area
        self.log_text = scrolledtext.ScrolledText(self.root, height=20)
        self.log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Start server button
        start_btn = tk.Button(self.root, text="Start Server", command=self.start_server)
        start_btn.pack(pady=10)

    def log(self, message):
        """Mencatat pesan di log area"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def start_server(self):
        """Memulai server dan menerima koneksi"""
        self.log(f"Server dimulai di {self.host}:{self.port}")
        threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        """Menerima koneksi dari client"""
        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, client_address)
                )
                client_thread.start()
            except Exception as e:
                self.log(f"Error menerima koneksi: {e}")
                break

    def handle_file_upload(self, client_socket, name):
        """Menangani proses upload file dengan lebih baik"""
        try:
            # Terima informasi file
            file_info = client_socket.recv(1024).decode('utf-8').strip()

            # Validasi input file_info
            if '|' not in file_info:
                raise ValueError("Format informasi file tidak valid")

            filename, filesize_str = file_info.split('|')

            # Menggunakan regex untuk memisahkan angka dari teks pada ukuran file
            match = re.match(r"(\d+)(\D*)", filesize_str)  # (\d+) untuk angka, (\D*) untuk teks
            if not match:
                raise ValueError(f"Ukuran file '{filesize_str}' tidak valid, harus berupa angka diikuti nama file")

            filesize = int(match.group(1))  # Mengambil angka dari hasil regex

            # Konfirmasi siap menerima file
            client_socket.send("READY".encode('utf-8'))

            # Pastikan nama file unik
            base, ext = os.path.splitext(filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            counter = 1
            while os.path.exists(filepath):
                filename = f"{base}_{counter}{ext}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                counter += 1

            # Terima file
            bytes_received = 0
            with open(filepath, 'wb') as f:
                while bytes_received < filesize:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    f.write(data)
                    bytes_received += len(data)

            self.log(f"File diterima: {filename} dari {name}")
            client_socket.send(f"File {filename} berhasil diunggah".encode('utf-8'))
            return filename
        except ValueError as ve:
            self.log(f"Error: {ve}")
            client_socket.send(f"Gagal: {ve}".encode('utf-8'))
            return None
        except Exception as e:
            self.log(f"Error upload file: {e}")
            client_socket.send("Gagal mengunggah file".encode('utf-8'))
            return None

    def handle_file_download(self, client_socket, filename):
        """Menangani proses download file dengan lebih baik"""
        try:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            if not os.path.exists(file_path):
                client_socket.send("FILE_NOT_FOUND".encode('utf-8'))
                return

            # Kirim konfirmasi file ditemukan dan ukuran file
            filesize = os.path.getsize(file_path)
            client_socket.send(f"FILE_FOUND|{filesize}".encode('utf-8'))

            # Tunggu konfirmasi klien
            response = client_socket.recv(1024).decode('utf-8')
            if response != "READY":
                return

            # Kirim file
            with open(file_path, "rb") as f:
                while chunk := f.read(4096):
                    client_socket.send(chunk)

            # Kirim penanda akhir file
            client_socket.send(b"FILE_TRANSFER_COMPLETE")
            self.log(f"File {filename} berhasil dikirim")
        except Exception as e:
            self.log(f"Error download file: {e}")
            client_socket.send("Gagal mengirim file".encode('utf-8'))

    def handle_client(self, client_socket, client_address):
        """Fungsi untuk menangani setiap klien"""
        try:
            # Terima nama klien
            name = client_socket.recv(1024).decode('utf-8')
            
            self.clients[name] = client_socket
            self.log(f"{name} terhubung dari {client_address}")

            while True:
                message = client_socket.recv(1024).decode('utf-8')

                if message.startswith("@"):
                    # Pesan pribadi (P2P)
                    target, msg = message[1:].split(" ", 1)
                    if target in self.clients:
                        self.clients[target].send(f"[{name}]: {msg}".encode('utf-8'))
                    else:
                        client_socket.send("User tidak ditemukan.".encode('utf-8'))

                elif message == "UPLOAD":
                    # Proses upload file
                    uploaded_filename = self.handle_file_upload(client_socket, name)
                    if uploaded_filename:
                        # Beri tahu semua client bahwa ada file baru
                        for client_name, client in self.clients.items():
                            if client_name != name:
                                client.send(f"File baru: {uploaded_filename} diunggah oleh {name}".encode('utf-8'))


                elif message == "!group":
                    # Tambahkan klien ke grup
                    if client_socket not in self.groups:
                        self.groups.append(client_socket)
                    client_socket.send("Anda bergabung ke grup.".encode('utf-8'))

                elif message.startswith("!g "):
                    # Kirim pesan ke grup
                    msg = message[3:]
                    for member in self.groups:
                        if member != client_socket:
                            member.send(f"[Group - {name}]: {msg}".encode('utf-8'))

                elif message == "!leave":
                    # Keluar dari grup
                    if client_socket in self.groups:
                        self.groups.remove(client_socket)
                    client_socket.send("Anda telah keluar dari grup.".encode('utf-8'))

                else:
                    client_socket.send("Perintah tidak dikenal.".encode('utf-8'))

        except (ConnectionResetError, BrokenPipeError):
            self.log(f"{name} terputus.")
            if name in self.clients:
                del self.clients[name]
            if client_socket in self.groups:
                self.groups.remove(client_socket)
            client_socket.close()

    def run(self):
        """Menjalankan server GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    server = ChatServer()
    server.run()
