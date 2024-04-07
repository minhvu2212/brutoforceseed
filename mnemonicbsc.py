import os
import itertools
from web3 import Web3
from eth_account import Account
from mnemonic import Mnemonic
# Kích hoạt tính năng Mnemonic của thư viện eth_account
Account.enable_unaudited_hdwallet_features()
# Kết nối với Binance Smart Chain
bsc = "https://bsc-dataseed.binance.org/"
web3 = Web3(Web3.HTTPProvider(bsc))

# Đảm bảo rằng chúng ta đã kết nối thành công
assert web3.is_connected(), "Failed to connect to Binance Smart Chain"

# Hàm để lấy địa chỉ ví từ seed
def get_address_from_seed(seed):
    acct = Account.from_mnemonic(seed)
    return acct.address

# Hàm để kiểm tra số dư BNB và lưu vào file nếu khác 0
def check_balance_and_save(mnemonic, file_path):
    seed = Mnemonic("english").to_seed(mnemonic)
    address = get_address_from_seed(mnemonic)
    balance = web3.eth.get_balance(address)
    balance_bnb = web3.from_wei(balance, 'ether')
    if balance_bnb > 0:
        with open(file_path, 'a') as file:
            file.write(f'Mnemonic: {mnemonic} - Address: {address} - Balance: {balance_bnb}\n')

# Lấy đường dẫn tuyệt đối của file mnemonic.txt trong cùng thư mục với script
mnemonic_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mnemonic.txt')

# Tạo cụm từ ghi nhớ mới
mnemo = Mnemonic("english")
mnemonic = mnemo.generate(strength=256)  # Tạo cụm từ ghi nhớ với độ mạnh 256 bit

# Kiểm tra và lưu cụm từ ghi nhớ nếu số dư BNB khác 0
check_balance_and_save(mnemonic, mnemonic_file_path)

# Constants for the brute force
WORDLIST_SIZE = 2048  # Number of words in the BIP39 wordlist
MISSING_WORDS = 3     # Number of words to brute force
KNOWN_WORDS = ["word1", "word2", "word3", "word4", "word5", "word6", "word7", "word8", "word9", "word10", "word11", "word12"]  # Replace with known words

# Get the BIP39 English wordlist
wordlist = Mnemonic("english").wordlist

# Generate all combinations of MISSING_WORDS words from the wordlist
combinations = itertools.combinations(wordlist, MISSING_WORDS)

# Function to insert missing words into the known words at the right positions
def insert_missing_words(known, missing, positions):
    for pos, word in zip(positions, missing):
        known.insert(pos, word)
    return known

# Known positions of the missing words (replace with actual positions)
missing_word_positions = [5, 7, 9]  # Example positions

# Try each combination of missing words
for missing_words in combinations:
    # Insert the missing words into the known words
    mnemonic_words = insert_missing_words(KNOWN_WORDS.copy(), missing_words, missing_word_positions)
    mnemonic = " ".join(mnemonic_words)
    
    # Check if the mnemonic is valid
    if Mnemonic("english").check(mnemonic):
        # Check balance and save to file if balance is not zero
        check_balance_and_save(mnemonic, mnemonic_file_path)
        break  # Stop after finding the first valid mnemonic