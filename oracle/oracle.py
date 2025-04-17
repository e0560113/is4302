from web3 import Web3, Account
import json
import os
import solcx

solcx.install_solc(os.getenv('SOLC_VERSION'))

class Oracle:

    def __init__(self):
        # Setup Registered Voters
        self.registered_voters = set()
        self.import_all_registered_voters(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'voter_db.json'))
        
        # Setup Blockchain Connection
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('W3_WEBSOCKET_URL')))
        if not self.w3.is_connected():
            raise Exception("Failed to connect to local blockchain")
        oracle_account = Account.from_key(os.getenv("ORACLE_ADMIN_PRIVATE_KEY"))
        self.oracle_address = oracle_account.address
        print(f"Oracle address: {self.oracle_address}")

        # Deploy Oracle Contract
        self.contract, self.oracle_contract_address = self._deploy_contract()
        print(f"Oracle contract address: {self.oracle_contract_address}")
        
    def _deploy_contract(self):
        try:
            # Load ABI and bytecode from the contracts directory
            contract_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'contracts', 'Oracle.sol')
            
            with open(contract_path, 'r') as file:
                contract_json = json.load(file)
                contract_abi = contract_json['abi']
                contract_bytecode = contract_json['bytecode']
            
            # Create contract instance for deployment
            contract = self.w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
            
            tx = contract.constructor().build_transaction({
                'from': self.oracle_address,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.oracle_address)
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=os.getenv("ORACLE_ADMIN_PRIVATE_KEY"))
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
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
                    self.registered_voters.add(voter["auth_key"])
            return True
        except Exception as e:
            print(f"Error registering voters: {e}")
            return False

    def authenticate_voter(self, voter_id, auth_key, voter_ethAddress):
        if auth_key not in self.registered_voters:
            return False, "Voter not registered or invalid authentication key", None
        
            # On‑chain registration
        tx = self.contract.functions.registerVoter(eth_address).build_transaction({
            'from': self.oracle_address,
            'gas': 200_000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.oracle_address)
        })
        signed = self.w3.eth.account.sign_transaction(
            tx, 
            private_key=os.getenv("ORACLE_ADMIN_PRIVATE_KEY")
        )
        receipt = self.w3.eth.wait_for_transaction_receipt(
            self.w3.eth.send_raw_transaction(signed.rawTransaction)
        )
        if receipt.status == 1:
            return True, "Registered on‐chain", eth_address
        else:
            return False, "Tx failed", None

    
    
