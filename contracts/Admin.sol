// SPDX-License-Identifier: MIT 
pragma solidity ^0.8.0;

import "./ElectionContract.sol";

contract Admin {
    address public admin;
    string[] public electionNames;
    mapping(string => ElectionContract) electionsList;

    event ElectionStarted(string indexed electionName, address indexed electionAddress);

    modifier adminOnly() {
        require(msg.sender == admin, "Only admin is authorised to perform this action.");
        _;
    }

    constructor (address authorisedAdmin) public {
        admin = authorisedAdmin;
    }

    function startElection(
        string memory _electionName, 
        string memory _electionDescription, 
        uint256 _startTime, 
        uint256 _endTime, 
        string[] memory _candidates, 
        string[] memory _regions
    ) public adminOnly() {
        require(_startTime > block.timestamp, "Start time must be in the future");
        require(_endTime > _startTime, "End time must be after start time");
        require(address(electionsList[_electionName]) == address(0), "Election name already exists");

        ElectionContract newElection = new ElectionContract(
            _electionName, 
            _electionDescription, 
            _startTime, 
            _endTime, 
            _candidates, 
            _regions 
        );
        
        electionsList[_electionName] = newElection;
        electionNames.push(_electionName);

        emit ElectionStarted(_electionName, address(newElection));
    }

    function getOngoingElections() public view returns (address[] memory) {
        address[] memory ongoing;
        
        for (uint i = 0; i < electionNames.length; i++) {
            ElectionContract election = electionsList[electionNames[i]];
            if (block.timestamp >= election.startTime() && block.timestamp <= election.endTime()) {
                ongoing.push(address(election));
            }
        }
        return ongoing;
    }

    function getElectionByName(string memory _electionName) public view returns (ElectionContract) {
        return electionsList[_electionName];
    }

    function getElectionNames() public view returns (string[] memory) {
        return electionNames;
    }
}