import tkinter as tk
from tkinter import ttk, scrolledtext
from threading import Thread
import random
from mnemonic import Mnemonic
from eth_account import Account as EthAccount
from web3 import Web3
import time
from solana.rpc.api import Client
from concurrent.futures import ThreadPoolExecutor
from solders.keypair import Keypair  
import hashlib
from solders.pubkey import Pubkey
# Constants for the blockchain types
BLOCKCHAIN_TYPES = {
    'ETH': {'web3': Web3(Web3.HTTPProvider('https://ethereum-rpc.publicnode.com/')), 'name': 'Ethereum'},
    'ETC': {'web3': Web3(Web3.HTTPProvider('https://etc.rivet.link/')), 'name': 'Ethereum Classic'},
    'BSC': {'web3': Web3(Web3.HTTPProvider('https://bsc-dataseed1.defibit.io/')), 'name': 'Binance Smart Chain'},
    'SOL': {'client': Client("https://api.mainnet-beta.solana.com"), 'name': 'Solana'},
}

# Activate the Mnemonic feature of the eth_account library
EthAccount.enable_unaudited_hdwallet_features()

# Constants for the brute force
WORDLIST_SIZE = 2048  # Number of words in the BIP39 wordlist
MISSING_WORDS = 12    # Number of words to brute force

# Get the BIP39 English wordlist
mnemo = Mnemonic("english")
wordlist = mnemo.wordlist

# Global variable to track whether brute force is in progress
brute_force_running = False

# Global variable to track the count of valid mnemonics found
valid_mnemonic_count = 0

# Function to log messages to the GUI
def log_message(message):
    log_area.insert(tk.END, message + "\n")
    log_area.see(tk.END)
    if "Valid mnemonic" in message:
        root.after(0, update_valid_count)

# Function to update the valid mnemonic count in the GUI
def update_valid_count():
    valid_count_label.config(text=f"Valid Mnemonics Found: {valid_mnemonic_count}")

# Function to log wallet information to the GUI and save to file
def log_and_save_wallet_info(wallet_info):
    wallet_area.insert(tk.END, wallet_info + "\n")
    wallet_area.see(tk.END)
    with open("wallet.txt", "a") as file:
        file.write(wallet_info + "\n")

# Function to generate mnemonic
def generate_mnemonic():
    missing_words = random.sample(wordlist, MISSING_WORDS)
    return " ".join(missing_words)

# Function to get wallet address from seed
def get_address_from_seed(seed, blockchain_type):
    acct = EthAccount.from_mnemonic(seed)
    if blockchain_type in BLOCKCHAIN_TYPES.keys():
        return acct.address
    else:
        return None  # Return None for unsupported blockchain types

# Function to check balance and save if balance > 0
import hashlib

def check_balance_and_save(seed, blockchain_type):
    if blockchain_type == 'SOL':
        solana_client = BLOCKCHAIN_TYPES['SOL']['client']
        try:
            # Sử dụng SHA-256 để băm seed đảm bảo nó có độ dài 32 byte
            seed_hash = hashlib.sha256(seed.encode()).digest()
            keypair = Keypair.from_seed(seed_hash)  # Sử dụng seed đã băm để tạo Keypair
            pubkey = keypair.pubkey()  # Lấy pubkey dưới dạng đối tượng Pubkey
            balance_response = solana_client.get_balance(pubkey)  # Sử dụng đối tượng Pubkey trực tiếp
            if balance_response.value > 0:
                sol_balance = balance_response.value / 1e9  # Chuyển đổi lamports sang SOL
                log_and_save_wallet_info(f"Found balance: {sol_balance} SOL in wallet {pubkey}")
        except Exception as e:
            log_message(f"Error checking Solana balance: {str(e)}")
    else:
        address = get_address_from_seed(seed, blockchain_type)
        blockchain_info = BLOCKCHAIN_TYPES[blockchain_type]
        if blockchain_info['web3']:
            try:
                balance = blockchain_info['web3'].eth.get_balance(address)
                eth_balance = blockchain_info['web3'].from_wei(balance, 'ether')
                if eth_balance > 0:
                    log_and_save_wallet_info(f"Found balance: {eth_balance} {blockchain_info['name']} in wallet {address}")
            except Exception as e:
                log_message(f"Error checking balance for {blockchain_info['name']}: {str(e)}")
                
# Brute force logic (simplified for demonstration)
def brute_force(attempts, selected_blockchains):
    global brute_force_running, valid_mnemonic_count
    brute_force_running = True
    valid_mnemonic_count = 0  # Reset the count at the start of a new brute force session
    with ThreadPoolExecutor(max_workers=int(threads_entry.get())) as executor:
        futures = []
        for _ in range(attempts):
            futures.append(executor.submit(brute_force_task, selected_blockchains))
        for future in futures:
            future.result()
    brute_force_running = False

def brute_force_task(selected_blockchains):
    global valid_mnemonic_count
    mnemonic = generate_mnemonic()
    if mnemo.check(mnemonic):
        log_message(f"Valid mnemonic: {mnemonic}")
        valid_mnemonic_count += 1  # Increment the valid mnemonic count
        for blockchain_type in selected_blockchains:
            check_balance_and_save(mnemonic, blockchain_type)
        return 1
    return 0  # Return 0 if mnemonic is invalid


# Function to start brute force
def start_brute_force():
    global brute_force_running
    if not brute_force_running:
        attempts = int(attempts_entry.get())
        selected_blockchains = [blockchain_type for blockchain_type, var in blockchain_vars.items() if var.get()]
        brute_force_thread = Thread(target=brute_force, args=(attempts, selected_blockchains))
        brute_force_thread.start()
    else:
        log_message("Brute force is already running.")

# GUI setup and remaining code
# The GUI setup and remaining code are the same as provided earlier

# GUI setup with ttk improvements
root = tk.Tk()
root.title("Brute Force Mnemonic")
root.geometry("800x600")

style = ttk.Style(root)
style.theme_use('clam')  # Sử dụng theme 'clam', bạn có thể thay đổi theme khác

# Main frame
main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill=tk.BOTH, expand=True)

# Log area for messages
log_label = ttk.Label(main_frame, text="Log Messages")
log_label.grid(row=0, column=0, pady=(0, 5), sticky='w')
log_area = scrolledtext.ScrolledText(main_frame, width=70, height=15)
log_area.grid(row=1, column=0, columnspan=3, pady=10)

# Log area for wallet information
wallet_label = ttk.Label(main_frame, text="Wallet Information")
wallet_label.grid(row=2, column=0, pady=(0, 5), sticky='w')
wallet_area = scrolledtext.ScrolledText(main_frame, width=70, height=5)
wallet_area.grid(row=3, column=0, columnspan=3, pady=10)

# Label for displaying the count of valid mnemonics found
valid_count_label = ttk.Label(main_frame, text="Valid Mnemonics Found: 0")
valid_count_label.grid(row=4, column=0, pady=5, sticky='w')

# Entry for number of attempts
attempts_label = ttk.Label(main_frame, text="Number of Attempts:")
attempts_label.grid(row=5, column=0, pady=5, sticky='w')
attempts_entry = ttk.Entry(main_frame)
attempts_entry.grid(row=5, column=1, pady=5, sticky='w')

# Entry for number of threads
threads_label = ttk.Label(main_frame, text="Number of Threads:")
threads_label.grid(row=6, column=0, pady=5, sticky='w')
threads_entry = ttk.Entry(main_frame)
threads_entry.grid(row=6, column=1, pady=5, sticky='w')

# Checkbuttons for selecting blockchains
blockchain_vars = {}
for i, blockchain_type in enumerate(BLOCKCHAIN_TYPES.keys()):
    var = tk.BooleanVar()
    blockchain_vars[blockchain_type] = var
    chk_btn = ttk.Checkbutton(main_frame, text=BLOCKCHAIN_TYPES[blockchain_type]['name'], variable=var)
    chk_btn.grid(row=7+i//2, column=i%2, sticky='w')

# Start button
start_button = ttk.Button(main_frame, text="Start Brute Force", command=start_brute_force)
start_button.grid(row=9, column=0, columnspan=2, pady=10)

root.mainloop()