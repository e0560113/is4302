import os
import json
import subprocess
import time
import signal
import contextlib
from pathlib import Path
from web3 import Web3, Account
from dotenv import load_dotenv
from oracle.oracle import Oracle
from utils.key_handler import generate_keypair, create_shamir_shares, encrypt_vote

load_dotenv()

ORACLE_ADMIN_PK = os.getenv("ORACLE_ADMIN_PRIVATE_KEY")
ELECTION_ADMIN_PK = os.getenv("ELECTION_ADMIN_PRIVATE_KEY")

def start_hardhat_node(host="127.0.0.1", port="8545"):
    print(f"Starting Hardhat node at {host}:{port}...")
    proc = subprocess.Popen(
        ["npx", "hardhat", "node", "--hostname", host, "--port", port],
        preexec_fn=os.setsid
    )
    time.sleep(2)
    return proc

def kill(proc):
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)


ARTIFACTS = Path("artifacts/contracts")
def load_artifact(name):
    artifact_path = ARTIFACTS / name
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    return json.loads(artifact_path.read_text())

def deploy(w3, artifact, private_key, *constructor_args):
    abi       = artifact["abi"]
    bytecode  = artifact["bytecode"]
    acct      = w3.eth.account.from_key(private_key)
    contract  = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    tx = contract.constructor(*constructor_args).build_transaction({
        "from":  acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas":   9_000_000,
        "gasPrice": w3.eth.gas_price,
    })
    signed = acct.sign_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(
        w3.eth.send_raw_transaction(signed.raw_transaction)
    )
    return w3.eth.contract(address=receipt.contractAddress, abi=abi)

def main():
    # Launch Hardhat Node
    host = os.getenv("CHAIN_RPC_HOST")
    port = os.getenv("CHAIN_RPC_PORT")
    node = start_hardhat_node(host, port)

    # Connect to Hardhat Node
    try:
        print(f"Connecting to {host}:{port}...")
        w3 = Web3(Web3.HTTPProvider(f"http://{host}:{port}"))
        time.sleep(5)
        
        if not w3.is_connected():
            print("Failed to connect to Hardhat JSON-RPC")
            return
            
        print("Successfully connected to Hardhat JSON-RPC")

        oracle_admin = Account.from_key(ORACLE_ADMIN_PK)
        election_admin = Account.from_key(ELECTION_ADMIN_PK)
        print(f"Oracle Admin Address: {oracle_admin.address}")
        print(f"Election Admin Address: {election_admin.address}")

        election_art = load_artifact("ElectionContract.sol/ElectionContract.json")

        oracle_instance = Oracle(w3=w3, private_key=ORACLE_ADMIN_PK)
        oracle_address = oracle_instance.oracle_contract_address
        
        now = w3.eth.get_block("latest")["timestamp"]
        
        # Election Contract Details
        election_name = os.getenv("ELECTION_NAME", "Default Election")
        election_desc = os.getenv("ELECTION_DESCRIPTION", "Default Description")
        start_delay = int(os.getenv("ELECTION_START_DELAY", "20"))
        duration = int(os.getenv("ELECTION_DURATION", "3600"))
        candidates = os.getenv("ELECTION_CANDIDATES", "").split(",")
        regions = os.getenv("ELECTION_REGIONS", "").split(",")
        print(f"Deploying election with: {election_name}, {len(candidates)} candidates, {len(regions)} regions")
        
        election = deploy(
            w3, 
            election_art,
            ELECTION_ADMIN_PK,
            election_name,
            election_desc,
            now + start_delay,
            now + start_delay + duration,
            candidates, 
            regions,  
            oracle_address
        )

        acct = w3.eth.account.from_key(ORACLE_ADMIN_PK)
        tx   = oracle_instance.contract.functions.setElection(election.address).build_transaction({
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gasPrice": w3.eth.gas_price,
        })
        w3.eth.send_raw_transaction(acct.sign_transaction(tx).raw_transaction)
        print("[ADDRESS] Oracle:", oracle_address)
        print("[ADDRESS] Election:", election.address)

        # Generate Shamir Secret
        n = int(os.getenv("ELECTION_N_TRUSTED_STAKEHOLDERS"))
        k = int(os.getenv("ELECTION_K_THRESHOLD"))
        public_key_tuple, private_key_tuple = generate_keypair()
        print("\nGenerated Key Pair:")
        pub_n, pub_e = public_key_tuple
        priv_n, priv_d = private_key_tuple
        print(f"Public Key (n): {pub_n}")
        print(f"Public Key (e): {pub_e}")

        shares = create_shamir_shares(priv_d, k, n)
        print("\nPrivate Key Shares (Integer parts):")
        shares_str = str(shares)
        print(shares_str)

        pub_n_bytes = pub_n.to_bytes((pub_n.bit_length() + 7) // 8, 'big')
        print(f"Setting Public Key (n={pub_n}, e={pub_e}) with n={n}, k={k} on Election contract...")
        print(f"Public Key Modulus (bytes): 0x{pub_n_bytes.hex()}")
        set_pk_tx = election.functions.setPublicKey(pub_n_bytes, n, k).build_transaction({
            "from": election_admin.address,
            "nonce": w3.eth.get_transaction_count(election_admin.address),
            "gas": 500_000,
            "gasPrice": w3.eth.gas_price,
        })
        signed_set_pk_tx = w3.eth.account.sign_transaction(set_pk_tx, private_key=ELECTION_ADMIN_PK)
        tx_hash = w3.eth.send_raw_transaction(signed_set_pk_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Public Key set successfully. Transaction hash: {receipt.transactionHash.hex()}")

        # Voter CLI
        while True:
            try:
                action = input("Enter action (authenticate/vote/exit): ").lower()
                if action == 'exit':
                    break
                elif action == 'authenticate':
                    voter_addr = input("Enter voter ETH address: ")
                    auth_key = input("Enter auth key: ")
                    
                    try:
                        success = oracle_instance.authenticate_voter(auth_key, voter_addr)
                        if success:
                            print(f"Authentication successful for {auth_key}")
                        else:
                            print(f"Authentication failed for {auth_key}")
                    except AttributeError:
                         print("Error: 'authenticate_voter' method not found on Oracle instance. Please check oracle.py.")
                    except Exception as e:
                        print(f"Authentication failed: {e}")

                elif action == 'vote':
                    voter_pk = input("Enter voter private key: ")
                    candidate_index = int(input("Enter candidate index: "))
                    
                    try:
                        voter_acct = w3.eth.account.from_key(voter_pk)
                        
                        # Get Public Key
                        print("Fetching public key modulus (n) from contract...")
                        n_bytes = election.functions.getPublicKey().call()
                        pub_n_contract = int.from_bytes(n_bytes, 'big')
                        
                        pub_e_contract = 65537
                        public_key_tuple = (pub_n_contract, pub_e_contract)
                        print(f"Using public key: n={pub_n_contract}, e={pub_e_contract}")
                        
                        # Encrypt the vote
                        vote_string = str(candidate_index) 
                        print(f"Encrypting vote '{vote_string}'...")
                        encrypted_vote = encrypt_vote(public_key_tuple, vote_string)
                        print(f"Encrypted vote (bytes): 0x{encrypted_vote.hex()}")
                        
                        # Send encrypted vote
                        vote_tx = election.functions.castVote(encrypted_vote).build_transaction({
                            "from": voter_acct.address,
                            "nonce": w3.eth.get_transaction_count(voter_acct.address),
                            "gas": 500_000,
                            "gasPrice": w3.eth.gas_price,
                        })
                        signed_vote_tx = voter_acct.sign_transaction(vote_tx)
                        vote_tx_hash = w3.eth.send_raw_transaction(signed_vote_tx.raw_transaction)
                        vote_receipt = w3.eth.wait_for_transaction_receipt(vote_tx_hash)
                        print(f"Vote cast successfully. Tx: {vote_receipt.transactionHash.hex()}")
                    except Exception as e:
                        print(f"Voting failed: {e}")
                else:
                    print("Invalid action. Use 'authenticate', 'vote', or 'exit'.")

            except KeyboardInterrupt:
                print("\nExiting voter CLI mode...")
                break
            except Exception as e:
                print(f"An error occurred: {e}")

        if action != 'exit':
             print("\nPress Ctrl+C to stop the Hardhat node and exit")
             while True:
                 try:
                     time.sleep(1)
                 except KeyboardInterrupt:
                     print("\nStopping Hardhat node...")
                     break
            
    except KeyboardInterrupt:
        print("\nStopping Hardhat node...")
    except Exception as e:
        print(f"Error in demo: {e}")
    finally:
        kill(node)
        print("Hardhat node stopped.")

if __name__ == "__main__":
    main()
