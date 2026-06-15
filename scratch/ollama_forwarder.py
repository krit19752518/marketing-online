import socket
import threading
import sys

def handle_client(client_socket):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect(('127.0.0.1', 11434))
    except Exception as e:
        print(f"[-] Failed to connect to local Ollama on 127.0.0.1:11434: {e}")
        client_socket.close()
        return

    def forward(src, dst):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                dst.sendall(data)
        except Exception:
            pass
        finally:
            src.close()
            dst.close()

    threading.Thread(target=forward, args=(client_socket, server_socket), daemon=True).start()
    threading.Thread(target=forward, args=(server_socket, client_socket), daemon=True).start()

def main():
    bind_ip = '172.17.0.1'
    bind_port = 11434
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((bind_ip, bind_port))
    except Exception as e:
        print(f"[-] Binding to {bind_ip}:{bind_port} failed: {e}")
        print("[*] Trying to bind to 0.0.0.0 instead...")
        try:
            server.bind(('0.0.0.0', bind_port))
        except Exception as e2:
            print(f"[-] Binding to 0.0.0.0 failed: {e2}")
            sys.exit(1)
            
    server.listen(10)
    print(f"[+] Port forwarder listening on {server.getsockname()[0]}:{bind_port} -> 127.0.0.1:11434...")
    try:
        while True:
            client_sock, addr = server.accept()
            handle_client(client_sock)
    except KeyboardInterrupt:
        print("\n[*] Shutting down port forwarder.")
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == '__main__':
    main()
