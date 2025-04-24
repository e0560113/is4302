from web3 import Web3, Account
import json
import os
import solcx
from dotenv import load_dotenv

load_dotenv()

SOLC_VERSION = os.getenv('SOLC_VERSION', '0.8.19')
solcx.install_solc(SOLC_VERSION)

class Oracle:

    def __init__(self, w3=None, contract_address=None, private_key=None):
        self.registered_voters = {}
        voter_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'voters.json')
        self.import_all_registered_voters(voter_db_path)
        
        if w3:
            self.w3 = w3
        else:
            websocket_url = os.getenv('W3_WEBSOCKET_URL')
            self.w3 = Web3(Web3.HTTPProvider(websocket_url))
            
        if not self.w3.is_connected():
            raise Exception("Failed to connect to local blockchain")
            
        self.private_key = private_key if private_key else os.getenv("ORACLE_ADMIN_PRIVATE_KEY")
        oracle_account = Account.from_key(self.private_key)
        self.oracle_address = oracle_account.address
        print(f"Oracle address: {self.oracle_address}")

        if contract_address:
            contract_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'artifacts', 'contracts', 'Oracle.sol', 'Oracle.json')
            with open(contract_path, 'r') as file:
                contract_json = json.load(file)
                contract_abi = contract_json['abi']
            self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
            self.oracle_contract_address = contract_address
            print(f"Using existing Oracle contract at address: {self.oracle_contract_address}")
        else:
            self.contract, self.oracle_contract_address = self._deploy_contract()
            print(f"Deployed new Oracle contract at address: {self.oracle_contract_address}")
        
    def _deploy_contract(self):
        try:
            contract_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'artifacts', 'contracts', 'Oracle.sol', 'Oracle.json')
            
            with open(contract_path, 'r') as file:
                contract_json = json.load(file)
                contract_abi = contract_json['abi']
                contract_bytecode = contract_json['bytecode']

            contract = self.w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
            
            tx = contract.constructor().build_transaction({
                'from': self.oracle_address,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.oracle_address)
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            print("Waiting for contract deployment transaction to be mined...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.oracle_contract_address = receipt.contractAddress
        
            self.contract = self.w3.eth.contract(address=self.oracle_contract_address, abi=contract_abi)
            return self.contract, self.oracle_contract_address
        except Exception as e:
            raise Exception(f"Failed to deploy contract: {str(e)}")

    def import_all_registered_voters(self, voter_db_path):
        try:
            with open(voter_db_path, 'r') as file:
                voter_data = json.load(file)
                for voter in voter_data:
                    # Store both auth_key and region
                    self.registered_voters[voter["auth_key"]] = voter["region"]
            print(f"Successfully loaded {len(self.registered_voters)} voters from {voter_db_path}")
            return True
        except Exception as e:
            print(f"Error registering voters: {e}")
            return False

    def authenticate_voter(self, auth_key, voter_eth_address):
        if auth_key not in self.registered_voters:
            return False, "Voter not registered or invalid authentication key", None
        
        region = self.registered_voters[auth_key]
        
        # On‑chain registration
        tx = self.contract.functions.registerVoter(voter_eth_address, region).build_transaction({
            'from': self.oracle_address,
            'gas': 200_000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.oracle_address)
        })
        signed = self.w3.eth.account.sign_transaction(
            tx, 
            private_key=self.private_key
        )
        receipt = self.w3.eth.wait_for_transaction_receipt(
            self.w3.eth.send_raw_transaction(signed.raw_transaction)
        )
        if receipt.status == 1:
            return True, "Registered on‐chain", voter_eth_address
        else:
            return False, "Tx failed", None

    
    
