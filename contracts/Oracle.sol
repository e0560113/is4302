// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Considerations: A lot of insecure stuff such as public list of addresses that can be viewed by public.
// Random strings used such as blockchain.timestamp can be manipulated by miners.

contract Oracle {
    address public oracleAdmin;
    
    // Store eligible users (managed off-chain)
    mapping(address => bool) public isEligible;
    
    // Verification codes for login
    mapping(address => bytes32) public verificationCodes;
    
    // JWTs for verified voters
    mapping(address => string) public userJWTs;

    event LoginRequest(address indexed user);
    event VoteVerified(address indexed user);
    event JWTGenerated(address indexed user);

    modifier onlyOracleAdmin() {
        require(msg.sender == oracleAdmin, "Not authorized");
        _;
    }

    constructor() {
        oracleAdmin = msg.sender;
    }

    // Off-chain Oracle should call this after verifying Singpass credentials
    function setEligibility(address user, bool status) external onlyOracleAdmin {
        isEligible[user] = status;
    }

    // Called by user to initiate login
    // off-chain oracle service: receives Singpass credentials, verifies against government database, calls setEligibility() and setVerificationCode() if valid
    function requestLogin() external {
        emit LoginRequest(msg.sender);
    }

    // Off-chain Oracle calls this after verification
    function setVerificationCode(address user, bytes32 code) external onlyOracleAdmin {
        verificationCodes[user] = code;
    }

    // Called after successful vote to request JWT
    // Off-chain oracle validates vote has occurred, generates JWT with user claims, calls setJWT() to store on-chain
    function requestJWT() external {
        require(bytes(userJWTs[msg.sender]).length == 0, "JWT already issued");
        emit VoteVerified(msg.sender);
    }

    // Off-chain Oracle calls this with generated JWT
    function setJWT(address user, string calldata jwt) external onlyOracleAdmin {
        userJWTs[user] = jwt;
        emit JWTGenerated(user);
    }
}