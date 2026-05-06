import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import websocket
import json

API_URL = "http://localhost:8000"

# глобальные переменные для ws и user_id
current_user_id = None
ws_conn = None


def update_status(text, color="black"):
    status_label.config(text=text, fg=color)


def on_ws_message(ws, message):
    data = json.loads(message)
    print(f"[ws] {data}")

    if data["status"] == "connected":
        update_status(f"Подключено: {data['protocol']}://{data['host']}:{data['port']}", "green")
    elif data["status"] == "disconnected":
        update_status("Отключено", "red")
    else:
        update_status(data["status"], "orange")


def on_ws_error(ws, error):
    print(f"[ws error] {error}")
    update_status("Ошибка WebSocket", "red")


def on_ws_close(ws, code, msg):
    print(f"[ws closed]")
    update_status("Соединение закрыто", "gray")


def start_ws(user_id):
    global ws_conn
    url = f"ws://localhost:8000/ws/status/{user_id}"
    print(f"[ws] connecting to {url}")
    ws_conn = websocket.WebSocketApp(
        url,
        on_message=on_ws_message,
        on_error=on_ws_error,
        on_close=on_ws_close,
    )
    ws_conn.run_forever()


def do_connect():
    global current_user_id, ws_conn

    key = key_entry.get().strip()
    if not key:
        messagebox.showwarning("Ошибка", "Введи ключ активации")
        return

    connect_btn.config(state="disabled")
    update_status("Подключаемся...", "orange")

    try:
        print(f"[connect] sending key={key}")
        r = requests.post(f"{API_URL}/api/activate-key", json={"key": key}, timeout=10)
        print(f"[connect] response {r.status_code}: {r.text}")

        if r.status_code == 200:
            data = r.json()
            current_user_id = data["user_id"]
            proxy_label.config(text=f"Прокси: {data['protocol']}://{data['host']}:{data['port']}")
            disconnect_btn.config(state="normal")
            key_entry.config(state="disabled")

            # запускаем websocket в отдельном потоке
            t = threading.Thread(target=start_ws, args=(current_user_id,), daemon=True)
            t.start()

        elif r.status_code == 503:
            update_status("Все прокси заняты, попробуй позже", "red")
            connect_btn.config(state="normal")
        else:
            msg = r.json().get("detail", "Ошибка")
            update_status(f"Ошибка: {msg}", "red")
            connect_btn.config(state="normal")

    except requests.exceptions.ConnectionError:
        update_status("Не могу подключиться к серверу", "red")
        connect_btn.config(state="normal")
    except Exception as e:
        print(f"[connect error] {e}")
        update_status(f"Ошибка: {e}", "red")
        connect_btn.config(state="normal")


def do_disconnect():
    global current_user_id, ws_conn

    if ws_conn:
        ws_conn.close()
        ws_conn = None

    if current_user_id:
        try:
            requests.post(f"{API_URL}/api/disconnect-by-user/{current_user_id}", timeout=5)
            print(f"[disconnect] user {current_user_id} disconnected")
        except Exception as e:
            print(f"[disconnect error] {e}")
        current_user_id = None

    update_status("Отключено", "red")
    proxy_label.config(text="Прокси: —")
    connect_btn.config(state="normal")
    disconnect_btn.config(state="disabled")
    key_entry.config(state="normal")
    key_entry.delete(0, tk.END)


# --- GUI ---

root = tk.Tk()
root.title("Proxy Client")
root.geometry("460x250")
root.resizable(False, False)

frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="Proxy Client", font=("Helvetica", 14, "bold")).pack(pady=(0, 12))

ttk.Label(frame, text="Ключ активации:").pack(anchor="w")
key_entry = ttk.Entry(frame, width=50)
key_entry.pack(fill="x", pady=(4, 10))

btn_frame = ttk.Frame(frame)
btn_frame.pack(fill="x")

connect_btn = ttk.Button(
    btn_frame, text="Подключиться",
    command=lambda: threading.Thread(target=do_connect, daemon=True).start()
)
connect_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

disconnect_btn = ttk.Button(btn_frame, text="Отключиться", command=do_disconnect, state="disabled")
disconnect_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

proxy_label = ttk.Label(frame, text="Прокси: —", font=("Courier", 10))
proxy_label.pack(pady=(12, 4), anchor="w")

status_label = tk.Label(frame, text="Ожидание", fg="gray", font=("Helvetica", 11))
status_label.pack(anchor="w")

root.mainloop()
