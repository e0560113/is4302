# is4302
blockchain voting system

## Setup

### 1. Prerequisites
- Ensure you have [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) installed.
- Ensure you have [Node.js](https://nodejs.org/en/download/) and npm installed.

### 2. Clone the Repository
```bash
git clone <your-repo-url>
cd is4302
```

### 3. Set up Conda Environment
Use the provided `environment.yml` file to create the Conda environment:
```bash
conda env create -f environment.yml
conda activate base 
```
*Note: The environment name might be different if you modified `environment.yml`.*

### 4. Set up Hardhat Project
Install the necessary Node.js dependencies for Hardhat:
```bash
npm install
```

### 5. Configure Environment Variables
Create a `.env` file by copying the example file:
```bash
cp .env.example .env
```
Then, open the `.env` file and fill in the required values, particularly:
- `ORACLE_ADMIN_PRIVATE_KEY`
- `ELECTION_ADMIN_PRIVATE_KEY`

Make sure the other settings like candidates, regions, etc., match your desired election configuration.

## Running the Demo

Once the setup is complete, you can run the election demo script:

```bash
python demo_election.py
```

This script will:
1. Start a local Hardhat blockchain node.
2. Deploy the `Oracle` and `ElectionContract` smart contracts.
3. Configure the contracts (set election address in Oracle, set public key in Election).
4. Generate Shamir shares for the election private key.
5. Enter an interactive loop allowing you to:
    - Authenticate voters (using predefined keys from `voters.json` or manually entered details).
    - Cast encrypted votes as an authenticated voter.
6. Press `Ctrl+C` during the interactive loop or type `exit` to stop the demo and shut down the Hardhat node.
