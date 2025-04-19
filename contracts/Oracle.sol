// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Voter.sol";
import "./ElectionContract.sol";

// Oracle contract that mimics Singpass verification and creates Voter contracts
contract Oracle {
    address public oracleAdmin;
    
    // Store eligible users (managed off-chain)
    mapping(address => bool) public isEligible;
    
    // Verification codes for login
    mapping(address => bytes32) public verificationCodes;
    
    // Track if voter contract has been created for an address
    mapping(address => bool) public hasVoterContract;
    
    // Mapping from user address to their voter contract address
    mapping(address => address) public voterContracts;
    
    // Mapping from region to election contract
    mapping(string => address) public electionsByRegion;
    
    // List of available regions
    string[] public availableRegions;

    event LoginRequest(address indexed user);
    event VerificationComplete(address indexed user, bool success);
    event VoterContractCreated(address indexed user, address voterContract);
    event RegionAdded(string region, address electionContract);

    modifier onlyOracleAdmin() {
        require(msg.sender == oracleAdmin, "Not authorized");
        _;
    }

    constructor() {
        oracleAdmin = msg.sender;
    }

    // Add a new election contract for a region
    function addElectionForRegion(string memory region, address electionContract) external onlyOracleAdmin {
        require(electionContract != address(0), "Invalid election contract address");
        require(bytes(region).length > 0, "Region cannot be empty");
        
        // Check if region already exists
        bool regionExists = false;
        for (uint i = 0; i < availableRegions.length; i++) {
            // Convert strings to hash values to compare using cryptographic hash function.
            if (keccak256(bytes(availableRegions[i])) == keccak256(bytes(region))) {
                regionExists = true;
                break;
            }
        }
        
        if (!regionExists) {
            availableRegions.push(region);
        }
        
        electionsByRegion[region] = electionContract;
        emit RegionAdded(region, electionContract);
    }

    // Off-chain Oracle should call this after verifying Singpass credentials
    function setEligibility(address user, bool status, string memory region) external onlyOracleAdmin {
        require(bytes(region).length > 0, "Region cannot be empty");
        require(electionsByRegion[region] != address(0), "Election for region not found");
        
        isEligible[user] = status;
        
        // Generate verification code if eligible
        if (status) {
            // Create a pseudo-random verification code based on user address and block data
            bytes32 verificationCode = keccak256(abi.encodePacked(user, block.timestamp, block.difficulty));
            verificationCodes[user] = verificationCode;
        }
        
        emit VerificationComplete(user, status);
    }

    // Called by user to initiate login and verification
    function requestVerification() external {
        emit LoginRequest(msg.sender);
        // Off-chain oracle service will listen for this event and verify the user's Singpass credentials
    }

    // Create a voter contract for a verified user
    function createVoterContract(string memory region) external returns (address) {
        require(isEligible[msg.sender], "User is not eligible to vote");
        require(!hasVoterContract[msg.sender], "Voter contract already created");
        require(electionsByRegion[region] != address(0), "Election for region not found");
        
        // Create new voter contract
        // eligibleToVote = 1 means eligible, hasVoted = 0 means has not voted yet
        Voter voterContract = new Voter(
            electionsByRegion[region],
            toString(msg.sender),
            1, // eligible to vote
            0  // has not voted yet
        );
        
        // Store the voter contract address
        voterContracts[msg.sender] = address(voterContract);
        hasVoterContract[msg.sender] = true;
        
        emit VoterContractCreated(msg.sender, address(voterContract));
        
        return address(voterContract);
    }
    
    // Get the voter contract address for a user
    function getVoterContract() external view returns (address) {
        require(hasVoterContract[msg.sender], "No voter contract created for this user");
        return voterContracts[msg.sender];
    }
    
    // Check if a user is eligible to vote
    function checkEligibility(address user) external view returns (bool) {
        return isEligible[user];
    }
    
    // Get verification code for a user
    function getVerificationCode(address user) external view onlyOracleAdmin returns (bytes32) {
        return verificationCodes[user];
    }
    
    // Get all available regions
    function getAvailableRegions() external view returns (string[] memory) {
        return availableRegions;
    }
    
    // Helper function to convert address to string
    function toString(address account) internal pure returns (string memory) {
        bytes32 value = bytes32(uint256(uint160(account)));
        bytes memory alphabet = "0123456789abcdef";
        
        bytes memory str = new bytes(42);
        str[0] = '0';
        str[1] = 'x';
        
        for (uint256 i = 0; i < 20; i++) {
            str[2 + i * 2] = alphabet[uint8(value[i + 12] >> 4)];
            str[3 + i * 2] = alphabet[uint8(value[i + 12] & 0x0f)];
        }
        
        return string(str);
    }
}