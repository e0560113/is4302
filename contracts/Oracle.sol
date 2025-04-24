// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Oracle {
    
    address public immutable oracleAdmin;
    address public election;
    mapping(address => uint8) public registeredVoters; // Stores registered voters and their respective regions(regions are mapped to predeterined values)

    event VoterRegistered(address indexed user, uint8 region);
    event ElectionSet(address indexed electionContract);

    modifier onlyOracleAdmin() {
        require(msg.sender == oracleAdmin, "Not authorized");
        _;
    }

    constructor() {
        oracleAdmin = msg.sender;
    }

    function setElection(address electionContract) external onlyOracleAdmin {
        require(election == address(0) && electionContract != address(0), "Election already set");
        election = electionContract;
        emit ElectionSet(electionContract);
    }

    function registerVoter(address voter, uint8 region) external onlyOracleAdmin {
        require(registeredVoters[voter] == 0, "Voter already registered");
        registeredVoters[voter] = region;
        emit VoterRegistered(voter, region);
    }
   
   function getVoterInfo(address user) external view returns (bool registered, uint8 region) {
        require(msg.sender == election, "Not authorized");
        registered = registeredVoters[user] != 0;
        region = registeredVoters[user];
        return (registered, region);
   }
}