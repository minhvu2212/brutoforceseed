import tkinter as tk
from tkinter import ttk, scrolledtext
from threading import Thread
import random
from mnemonic import Mnemonic
from eth_account import Account as EthAccount
from web3 import Web3
from solana.rpc.api import Client
from solders.keypair import Keypair  
import hashlib
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import os

# Constants for the blockchain types
BLOCKCHAIN_TYPES = {
    'ETH': {
        'endpoints': [
                       'https://ethereum-rpc.publicnode.com',
                       'https://rpc.immutable.com'
                     ],
        'name': 'ETH',
        'web3': True
    },
    'ETC': {
        'endpoints': [
                     'https://etc.rivet.link/',
                      'https://geth-at.etc-network.info',
                      'https://etc.etcdesktop.com'
                      ],
        'name': 'ETC',
        'web3': True
    },
    'BSC': {
        'endpoints': [
                     'https://bsc-dataseed.binance.org/',
                    'https://bsc-dataseed2.defibit.io',
                     'https://bsc.nodereal.io/',
                      'https://bsc-dataseed3.defibit.io', 
                      'https://bsc-dataseed1.defibit.io'
                      ],
        'name': 'BSC',
        'web3': True
    },
#    'SOL': {
 #       'endpoints': ['https://api.mainnet-beta.solana.com'],
 #       'name': 'Solana',
 #       'web3': False
 #   },
    'ARB': {
        'endpoints': [
            'https://arb1.arbitrum.io/rpc',
            'https://rpc.ankr.com/arbitrum'
           # 'https://arbitrum.llamarpc.com', X
           
           
        ],
        'name': 'Arbitrum',
        'web3': True
    },
    'BASE': {
        'endpoints': [
            'https://base-rpc.publicnode.com'
        ],
        'name': 'Base',
        'web3': True
    },
    'POLYGON': {
        'endpoints': [
           # 'https://polygon-rpc.com',
           'https://polygon-bor-rpc.publicnode.com',
           'wss://polygon-bor-rpc.publicnode.com'
        ],
        'name': 'Polygon',
        'web3': True
    },
}

# Kích hoạt tính năng Mnemonic của thư viện eth_account
EthAccount.enable_unaudited_hdwallet_features()

# Constants for the brute force
WORDLIST_SIZE = 2048  # Số lượng từ trong danh sách từ BIP39
MISSING_WORDS = 12    # Số lượng từ cần brute force

# Lấy danh sách từ tiếng Anh BIP39
mnemo = Mnemonic("english")
wordlist = mnemo.wordlist

# Biến toàn cục để theo dõi trạng thái brute force
brute_force_running = False

# Biến toàn cục để theo dõi số lượng mnemonics hợp lệ được tìm thấy
valid_mnemonic_count = 0

# Hàm để ghi log vào GUI
def log_message(message):
    log_area.insert(tk.END, message + "\n")
    log_area.see(tk.END)
    if "Valid mnemonic" in message:
        root.after(0, update_valid_count)

# Hàm để cập nhật số lượng mnemonics hợp lệ trong GUI
def update_valid_count():
    valid_count_number_label.config(text=f"{valid_mnemonic_count}", foreground="red")

# Hàm để ghi thông tin ví vào GUI và lưu vào tệp
def log_and_save_wallet_info(wallet_info):
    wallet_area.insert(tk.END, wallet_info + "\n")
    wallet_area.see(tk.END)
    with open("wallet.txt", "a") as file:
        file.write(wallet_info + "\n")

# Hàm để tạo mnemonic
def generate_mnemonic():
    missing_words = random.sample(wordlist, MISSING_WORDS)
    return " ".join(missing_words)

# Hàm để lấy địa chỉ ví từ seed cho các blockchain tương thích Ethereum
def get_address_from_seed(seed):
    acct = EthAccount.from_mnemonic(seed)
    return acct.address

# Hàm kiểm tra số dư và lưu nếu số dư > 0 cho Solana
async def check_solana_balance_and_save(session, seed):
    solana_client = BLOCKCHAIN_TYPES['SOL']['endpoints'][0]  # Sử dụng endpoint đầu tiên cho Solana
    try:
        seed_hash = hashlib.sha256(seed.encode()).digest()
        keypair = Keypair.from_seed(seed_hash)
        pubkey = keypair.pubkey()
        log_message(f"Checked for {seed}")
        async with session.post(solana_client, json={"method": "getBalance", "params": [str(pubkey)], "id": 1, "jsonrpc": "2.0"}) as response:
            result = await response.json()
            if result['result']['value'] > 0:
                sol_balance = result['result']['value'] / 1e9
                log_and_save_wallet_info(f"Found balance: {sol_balance} SOL in wallet {pubkey}")
    except Exception as e:
        log_message(f"Error checking Solana balance: {str(e)}")

# Hàm kiểm tra số dư và lưu nếu số dư > 0 cho EVM chains
async def check_evm_balance_and_save(session, seed, blockchain_type):
    address = get_address_from_seed(seed)
    endpoints = BLOCKCHAIN_TYPES[blockchain_type]['endpoints']
    for attempt in range(len(endpoints)):
        endpoint = random.choice(endpoints)
        try:
            log_message(f"Checked for {seed}")
            async with session.post(endpoint, json={"jsonrpc":"2.0","method":"eth_getBalance","params":[address, "latest"],"id":1}) as response:
                result = await response.json()
                balance = int(result['result'], 16)
                eth_balance = balance / 1e18  # Chuyển đổi Wei sang Ether
                if eth_balance > 0:
                    log_and_save_wallet_info(f"Found balance: {eth_balance} {BLOCKCHAIN_TYPES[blockchain_type]['name']} in wallet {address}")
                return  # Thoát khỏi vòng lặp nếu thành công
        except Exception as e:
            if 'Too Many Requests' in str(e):
                log_message(f"Too many requests for {endpoint}, retrying with another endpoint...")
                await asyncio.sleep(random.uniform(1, 3))  # Chờ một chút trước khi thử lại
            else:
                log_message(f"Error checking balance for {BLOCKCHAIN_TYPES[blockchain_type]['name']} at {endpoint}: {str(e)}")

# Logic brute force
async def brute_force_task(session, selected_blockchains, executor):
    global valid_mnemonic_count
    mnemonic = generate_mnemonic()
    if mnemo.check(mnemonic):
        log_message(f"Valid mnemonic: {mnemonic}")
        valid_mnemonic_count += 1  # Tăng số lượng mnemonics hợp lệ
        tasks = []
        for blockchain_type in selected_blockchains:
            if blockchain_type == 'SOL':
                tasks.append(check_solana_balance_and_save(session, mnemonic))
            else:
                tasks.append(check_evm_balance_and_save(session, mnemonic, blockchain_type))
        await asyncio.gather(*tasks)

async def brute_force(attempts, selected_blockchains, max_workers):
    global brute_force_running
    async with aiohttp.ClientSession() as session:
        tasks = [brute_force_task(session, selected_blockchains, None) for _ in range(attempts)]
        await asyncio.gather(*tasks)
    brute_force_running = False  # Đặt brute_force_running thành False khi quá trình hoàn thành

# Hàm để bắt đầu brute force
def start_brute_force():
    global brute_force_running
    if not brute_force_running:
        brute_force_running = True
        attempts = int(attempts_entry.get())
        max_workers = int(threads_entry.get())
        selected_blockchains = [blockchain_type for blockchain_type, var in blockchain_vars.items() if var.get()]
        brute_force_thread = Thread(target=lambda: asyncio.run(brute_force(attempts, selected_blockchains, max_workers)))
        brute_force_thread.start()
    else:
        log_message("Brute force is already running.")

# Hàm để dừng brute force
def stop_brute_force():
    global brute_force_running
    if brute_force_running:
        brute_force_running = False
        log_message("Brute force stopped.")

# Lấy số lượng lõi CPU
cpu_count = os.cpu_count()

# Cài đặt GUI
root = tk.Tk()
root.title("Coin Miner")
root.geometry("900x520")

# Thay đổi màu nền và phông chữ
root.configure(bg="#2f2f2f")  # Màu nền mới
font_style = ("Söhne", 11)
header_font_style = ("Söhne", 16, "bold")

# Tên
name_label = ttk.Label(root, text="COIN MINER (R)", background="#2f2f2f", foreground="#ececec", font=header_font_style)  # Màu chữ mới
name_label.grid(row=0, column=0, pady=10, padx=10, sticky='w')

# Khu vực thông tin chung
info_label = ttk.Label(root, text="Information", background="#2f2f2f", foreground="#ececec", font=font_style)
info_label.grid(row=1, column=0, pady=5, padx=10, sticky='w')

version_label = ttk.Label(root, text="Version: 1.011", background="#2f2f2f", foreground="#ececec", font=font_style)
version_label.grid(row=0, column=1, pady=5, padx=10, sticky='w')

# Số lần thử và số luồng
attempts_label = ttk.Label(root, text="Number of Attempts", background="#2f2f2f", foreground="#ececec", font=font_style)
attempts_label.grid(row=6, column=0, pady=5, padx=10, sticky='w')
attempts_entry = ttk.Entry(root, font=font_style)
attempts_entry.grid(row=6, column=1, pady=5, padx=10, sticky='w')

threads_label = ttk.Label(root, text="Number of Threads", background="#2f2f2f", foreground="#ececec", font=font_style)
threads_label.grid(row=7, column=0, pady=5, padx=10, sticky='w')
threads_entry = ttk.Entry(root, font=font_style)
threads_entry.grid(row=7, column=1, pady=5, padx=10, sticky='w')

# Nhãn đề xuất số lượng threads tối đa
max_threads_label = ttk.Label(root, text=f"Max: {cpu_count}", background="#2f2f2f", foreground="red", font=font_style)
max_threads_label.grid(row=8, column=1, pady=5, padx=10, sticky='w')

# Khu vực chọn blockchain
blockchain_label = ttk.Label(root, text="Select Blockchains", background="#2f2f2f", foreground="#ececec", font=font_style)
blockchain_label.grid(row=2, column=0, pady=5, padx=10, sticky='w')
style = ttk.Style()
style.configure("TCheckbutton", background="#2f2f2f", foreground="#ececec")

blockchain_vars = {}
columns = 2  # Số cột để chia
for i, blockchain_type in enumerate(BLOCKCHAIN_TYPES.keys()):
    var = tk.BooleanVar()
    blockchain_vars[blockchain_type] = var
    chk_btn = ttk.Checkbutton(root, text=BLOCKCHAIN_TYPES[blockchain_type]['name'], variable=var, style="TCheckbutton")  # Sử dụng style mặc định
    chk_btn.grid(row=3 + i // columns, column=i % columns, pady=5, padx=10, sticky='w')

# Nhãn để hiển thị số lượng mnemonics hợp lệ được tìm thấy và nhãn phụ để hiển thị số đếm
valid_count_frame = ttk.Frame(root, style="TFrame")
valid_count_frame.grid(row=1, column=2, columnspan=2, pady=10, padx=10, sticky='w')

valid_count_label = ttk.Label(valid_count_frame, text="Valid Mnemonics Found:", background="#2f2f2f", foreground="#ececec", font=font_style)
valid_count_label.pack(side=tk.LEFT)

valid_count_number_label = ttk.Label(valid_count_frame, text="0", background="#2f2f2f", foreground="red", font=font_style)
valid_count_number_label.pack(side=tk.LEFT)

style.configure("ButtonFrame.TFrame", background="#2f2f2f")

# Tạo frame với kiểu giao diện đã được định nghĩa
button_frame = ttk.Frame(root, style="ButtonFrame.TFrame")
button_frame.grid(row=9, column=0, columnspan=2, pady=10)

# Tạo một kiểu giao diện mới với kiểu dáng 3D
style.configure("RaisedButton.TButton", relief="raised")

# Tạo nút "Start" với kiểu giao diện đã được định nghĩa
start_button = ttk.Button(button_frame, text="Start", command=start_brute_force, width=15, style="RaisedButton.TButton")
start_button.grid(row=0, column=0, pady=5, padx=10, sticky='e')

# Tạo nút "Stop" với kiểu giao diện đã được định nghĩa
stop_button = ttk.Button(button_frame, text="Stop", command=stop_brute_force, width=15, style="RaisedButton.TButton")
stop_button.grid(row=1, column=0, pady=5, padx=10, sticky='w')

# Khu vực log
#log_label = ttk.Label(root, text="Log Messages", background="#2f2f2f", foreground="#ececec", font=font_style)
#log_label.grid(row=1, column=2, pady=5, padx=10, sticky='w')
log_area = scrolledtext.ScrolledText(root, width=80, height=13, bg="#0d0d0d", fg="#ececec", font=("Helvetica", 8), wrap=tk.WORD)  # Đổi màu nền và chữ
log_area.grid(row=2, column=2, rowspan=6, pady=5, padx=10, sticky='nw')

# Khu vực thông tin ví
wallet_label = ttk.Label(root, text="Wallet Information", background="#2f2f2f", foreground="#ececec", font=font_style)
wallet_label.grid(row=8, column=2, pady=5, padx=10, sticky='w')
wallet_area = scrolledtext.ScrolledText(root, width=80, height=7, bg="#0d0d0d", fg="#ececec", font=("Helvetica", 8), wrap=tk.WORD)  # Đổi màu nền và chữ
wallet_area.grid(row=9, column=2, pady=5, padx=10, sticky='nw')

root.mainloop()
