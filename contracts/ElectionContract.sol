// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Oracle.sol";

contract ElectionContract {
    struct Ballot {
        bytes encryptedVote;
        uint256 region;
    }
    
    address public electionAdmin;
    string public electionName;
    string public electionDescription;
    uint256 public startTime;
    uint256 public endTime;
    string[] public candidates;
    string[] public regions;
    address public electionOracle;
    address[] public votedAddresses;
    mapping(address => Ballot) public ballots;

    bytes public publicKey;
    bool public privateKeyPublished; 
    bytes public privateKey;      
    uint256 public n_trusted_stakeholders;
    uint256 public k_threshold;

    event PrivateKeyPublished(bytes privateKey);
    event PublicKeySet(bytes publicKey);

    modifier onlyAdmin() {
        require(msg.sender == electionAdmin, "Only admin can perform this action");
        _;
    }

    constructor(string memory _electionName, string memory _electionDescription, uint256 _startTime, uint256 _endTime, string[] memory _candidates, string[] memory _regions, address _electionOracle) {
        electionAdmin = msg.sender;
        electionName = _electionName;
        electionDescription = _electionDescription;
        startTime = _startTime;
        endTime = _endTime;
        candidates = _candidates;
        regions = _regions;
        electionOracle = _electionOracle;
        votedAddresses = new address[](0);

        // Key Management
        publicKey = "";
        privateKey = bytes("");
        privateKeyPublished = false;
    }

    function castVote(bytes memory _encryptedVote) public {
        require(block.timestamp >= startTime && block.timestamp <= endTime, "Election is not active.");

        require(ballots[msg.sender].encryptedVote.length == 0, "You have already cast a ballot");
        require(publicKey.length > 0, "Public key has not been set");

        (bool registered, uint8 region) = Oracle(electionOracle).getVoterInfo(msg.sender);
        require(registered, "You are not registered to vote in this election");

        votedAddresses.push(msg.sender);
        ballots[msg.sender] = Ballot({
            encryptedVote: _encryptedVote,
            region: region
        });
    }

    function collectBallots() public view returns (Ballot[] memory) {
        Ballot[] memory allBallots = new Ballot[](votedAddresses.length);
        
        for (uint256 i = 0; i < votedAddresses.length; i++) {
            allBallots[i] = ballots[votedAddresses[i]];
        }
        
        return allBallots;
    }

    // Key Management
    function setPublicKey(bytes memory _publicKey, uint256 _n_trusted_stakeholders, uint256 _k_threshold) public onlyAdmin {
        require(block.timestamp < startTime, "Cannot change public key after election has started");
        publicKey = _publicKey;
        n_trusted_stakeholders = _n_trusted_stakeholders;
        k_threshold = _k_threshold;
        emit PublicKeySet(_publicKey);
    }

    function getPublicKey() public view returns (bytes memory) {
        require(publicKey.length > 0, "Public key has not been set");
        return publicKey;
    }


    function revealPrivateKey(bytes memory _reconstructedPrivateKey) public onlyAdmin {
        require(block.timestamp > endTime, "Cannot reveal private key before election ends");
        require(!privateKeyPublished, "Private key has already been published");
        require(_reconstructedPrivateKey.length > 0, "Private key cannot be empty");

        privateKey = _reconstructedPrivateKey;
        privateKeyPublished = true;
        
        emit PrivateKeyPublished(privateKey);
    }
}